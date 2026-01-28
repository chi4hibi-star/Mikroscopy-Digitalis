from threading import Event, Lock, Thread
from queue import Queue, Full, Empty
from pygame import surfarray
from cv2 import calcHist
from numpy import stack
from picamera2 import Picamera2
#from libcamera import controls         #for camara parameter from settings

class CameraThread:
    def __init__(self, histogram_interval: int = 3):
        '''
        Pi Camera thread with histogram calculation
        histogram_interval: calculate histogram every N frames
        '''
        self.histogram_interval = histogram_interval
        self.cam = None
        self._thread = None
        self._stop_event = Event()
        self._pause_event = Event()
        self._frame_queue = Queue(maxsize=2)
        self._histogram_queue = Queue(maxsize=1)
        self._lock = Lock()
        self.is_running = False
        self.is_paused = False
        self._frame_counter = 0
        return
    
    def start(self)->bool:
        if self.is_running:
            return True
        if not self._initialize_camera():
            return False
        self._stop_event.clear()
        self._pause_event.clear()
        self._thread = Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self.is_running = True
        print("Pi Camera thread started")
        return True
    
    def _initialize_camera(self):
        try:
            with self._lock:
                self.cam = Picamera2()
                config = self.cam.create_preview_configuration()
                self.cam.configure(config)
                self.cam.start()
                self.cam.set_controls({"AeEnable": True, "AwbEnable": True})
            return True
        except Exception as e:
            self.last_error = f"Pi Camera initialization failed: {e}"
            print(self.last_error)
            return False
    
    def pause(self)->None:
        """Pause frame capture without stopping the camera"""
        self.is_paused = True
        self._pause_event.set()
        return
    
    def resume(self):
        """Resume frame capture"""
        self.is_paused = False
        self._pause_event.clear()
        return
    
    def _calculate_histogram(self, img_array):
        try:
            if len(img_array.shape) == 2:
                hist = calcHist([img_array], [0], None, [256], [0, 256])
                return [hist]
            elif len(img_array.shape) == 3:
                hist = [
                    calcHist([img_array], [0], None, [256], [0, 256]),  # Red
                    calcHist([img_array], [1], None, [256], [0, 256]),  # Green
                    calcHist([img_array], [2], None, [256], [0, 256])   # Blue
                ]
                return hist
        except Exception as e:
            print(f"Error calculating histogram: {e}")
            return None
    
    def _capture_loop(self):
        print(f"Capture loop started for Pi Camera")
        while not self._stop_event.is_set():
            try:
                if self._pause_event.is_set():
                    self._pause_event.wait(timeout=0.2)
                    continue
                with self._lock:
                    img_array = self._capture_frame
                if img_array is not None:
                    surface = surfarray.make_surface(img_array)
                    try:
                        self._frame_queue.put_nowait(surface)
                    except Full:
                        try:
                            self._frame_queue.get_nowait()
                            self._frame_queue.put_nowait(surface)
                        except Empty:
                            pass
                    self._frame_counter += 1
                    if self._frame_counter >= self.histogram_interval:
                        self._frame_counter = 0
                        hist = self._calculate_histogram(img_array)
                        if hist is not None:
                            try:
                                try:
                                    self._histogram_queue.get_nowait()
                                except Empty:
                                    pass
                                self._histogram_queue.put_nowait(hist)
                            except Full:
                                pass
            except Exception as e:
                print(f"Error in capture loop: {e}")
                self.last_error = str(e)
        print("Capture loop ended")
        return 
    
    def _capture_frame(self):
        if self.cam is None:
            return None
        try:
            img_array = self.cam.capture_array("main")
            if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                pass
            if len(img_array.shape) == 2:
                img_array = stack([img_array] * 3, axis=-1)
            return img_array
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None
    
    def get_frame(self):
        try:
            frame = self._frame_queue.get_nowait()
            return frame
        except Empty:
            return None
    
    def get_histogram(self):
        try:
            hist = self._histogram_queue.get_nowait()
            return hist
        except Empty:
            return None
        
    def stop(self):
        if not self.is_running:
            return
        print("Stopping camera thread...")
        self._stop_event.set()
        self._pause_event.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        self._cleanup_camera()
        self.is_running = False
        print("Camera thread stopped")
        return
    
    def _cleanup_camera(self):
        try:
            with self._lock:
                if self.cam is not None:
                    self.cam.stop()
                    self.cam.close()
                    self.cam = None
        except Exception as e:
            print(f"Error during camera cleanup: {e}")
        return
    
    def __del__(self):
        if self.is_running:
            self.stop()
        return