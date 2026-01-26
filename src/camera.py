from threading import Event,Lock,Thread
from queue import Queue,Full,Empty
from pygame import surfarray
from cv2 import cvtColor, COLOR_BGR2RGB, COLOR_RGB2BGR, flip, calcHist
from numpy import flip, stack, frombuffer, uint8
from gxipy_local import DeviceManager
from pyueye.ueye import (HIDS, is_InitCamera, IS_SUCCESS, IS_CM_BGR8_PACKED,
                             is_SetColorMode, IS_RECT, is_AOI, IS_AOI_IMAGE_GET_AOI,
                             sizeof, c_mem_p, is_AllocImageMem, is_SetImageMem,
                             is_FreezeVideo, IS_WAIT, c_char, is_ExitCamera)
from ctypes import c_int as eyeint

class CameraThread:
    def __init__(self, camera_type: str = "Daheng", histogram_interval: int = 3):
        '''
        supported camera_types are: Daheng, iDS
        histogram_interval: calculate histogram every N frames
        '''
        self.camera_type = camera_type
        self.histogram_interval = histogram_interval
        self.cam = None
        self._thread = None
        self._stop_event = Event()
        self._frame_queue = Queue(maxsize=2)
        self._histogram_queue = Queue(maxsize=1)
        self._lock = Lock()
        self.camwidth = None
        self.camheight = None
        self.mem_ptr = None
        self.mem_id = None
        self.is_running = False
        self.last_error = None
        self._frame_counter = 0
        return
    
    def start(self):
        if self.is_running:
            return True
        if not self._initialize_camera():
            return False
        self._stop_event.clear()
        self._thread = Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self.is_running = True
        print(f"Camera thread started for {self.camera_type}")
        return True
    
    def _initialize_camera(self):
        try:
            if self.camera_type == "Daheng":
                return self._initialize_daheng()
            elif self.camera_type == "iDS":
                return self._initialize_ids()
            else:
                self.last_error = f"Unknown camera type: {self.camera_type}"
                return False
        except Exception as e:
            self.last_error = f"Camera initialization failed: {e}"
            print(self.last_error)
            return False
    
    def _initialize_daheng(self):
        with self._lock:
            device_manager = DeviceManager()
            num, _ = device_manager.update_device_list()
            if num == 0:
                self.last_error = "No Daheng camera found"
                return False
            self.cam = device_manager.open_device_by_index(0)
            self.cam.stream_on()
        return True
    
    def _initialize_ids(self):
        with self._lock:
            self.cam = HIDS(0)
            ret = is_InitCamera(self.cam, None)
            if ret != IS_SUCCESS:
                self.last_error = "Could not initialize iDS camera"
                return False
            bits_per_pixel = 24
            color_mode = IS_CM_BGR8_PACKED
            ret = is_SetColorMode(self.cam, color_mode)
            if ret != IS_SUCCESS:
                self.last_error = "Could not set color mode"
                return False
            rect_aoi = IS_RECT()
            is_AOI(self.cam, IS_AOI_IMAGE_GET_AOI, rect_aoi, sizeof(rect_aoi))
            self.camwidth = int(rect_aoi.s32Width)
            self.camheight = int(rect_aoi.s32Height)
            self.mem_ptr = c_mem_p()
            self.mem_id = eyeint()
            is_AllocImageMem(self.cam, self.camwidth, self.camheight, 
                            bits_per_pixel, self.mem_ptr, self.mem_id)
            is_SetImageMem(self.cam, self.mem_ptr, self.mem_id)
        return True
    
    def _calculate_histogram(self, img_array):
        try:
            bgr_frame = cvtColor(img_array, COLOR_RGB2BGR)
            if len(bgr_frame.shape) == 2:
                hist = calcHist([bgr_frame], [0], None, [256], [0, 256])
                return [hist]
            elif len(bgr_frame.shape) == 3:
                hist = [
                    calcHist([bgr_frame], [0], None, [256], [0, 256]),  # Blue
                    calcHist([bgr_frame], [1], None, [256], [0, 256]),  # Green
                    calcHist([bgr_frame], [2], None, [256], [0, 256])   # Red
                ]
                return hist
        except Exception as e:
            print(f"Error calculating histogram: {e}")
            return None
    
    def _capture_loop(self):
        print(f"Capture loop started for {self.camera_type}")
        while not self._stop_event.is_set():
            try:
                with self._lock:
                    if self.camera_type == "Daheng":
                        img_array = self._capture_daheng_frame()
                    elif self.camera_type == "iDS":
                        img_array = self._capture_ids_frame()
                    else:
                        break
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
    
    def _capture_daheng_frame(self):
        if self.cam is None:
            return None
        frame = self.cam.data_stream[0].get_image()
        if frame is None:
            return None
        img_array = frame.get_numpy_array()
        img_array = flip(img_array, axis=0)
        if len(img_array.shape) == 2:
            img_array = stack([img_array] * 3, axis=-1)
        return img_array
    
    def _capture_ids_frame(self):
        if self.cam is None or self.mem_ptr is None:
            return None
        ret = is_FreezeVideo(self.cam, IS_WAIT)
        if ret != IS_SUCCESS:
            return None
        buffer_size = self.camheight * self.camwidth * 3
        img_array = frombuffer(
            (c_char * buffer_size).from_address(int(self.mem_ptr.value)),
            dtype=uint8
        ).reshape((self.camheight, self.camwidth, 3))
        img_array = cvtColor(img_array, COLOR_BGR2RGB)
        img_array = flip(img_array, axis=0)
        return img_array
    
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
                    if self.camera_type == "Daheng":
                        self.cam.stream_off()
                        self.cam.close_device()
                    elif self.camera_type == "iDS":
                        is_ExitCamera(self.cam)
                    self.cam = None
        except Exception as e:
            print(f"Error during camera cleanup: {e}")
        return
    
    def __del__(self):
        if self.is_running:
            self.stop()
        return