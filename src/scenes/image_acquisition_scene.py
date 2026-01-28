from pygame import VIDEORESIZE,surfarray,image
from pathlib import Path
from shutil import rmtree
from datetime import datetime
from ..windows.file_viewer import FileViewer
from ..windows.menu_bar import MenuBar
from ..windows.camera_view import CameraView
from ..windows.control_panel import ControlPanel
from ..windows.histogram_view import HistogramView
from ..camera import CameraThread
from typing import Tuple

class ImageAcquisitionScene():
    def __init__(self,screen,settings,switch_scene_callback):
        self.settings = settings
        self.switch_scene_callback = switch_scene_callback

        self.setup_menu_bar()
        self.setup_camera_view()
        self.setup_histogram_view()
        self.setup_control_panel()
        self.setup_file_viewer()
        self.setup_working_directory()

        self.update_layout(screen.get_size())

        self.live_frame = None
        self.camera_thread = None
        self.init_camera()
        self._prev_file_selection = []
        return
    
    def update_layout(self,window_size:Tuple[int,int])->None:
        self.menu_bar.update_layout(window_size)
        self.camera_view.update_layout(window_size)
        self.histogram_view.update_layout(window_size)
        self.control_panel.update_layout(window_size)
        self.file_viewer.update_layout(window_size)
        return

    def handle_events(self,events:list)->None:
        resize_events = [e for e in events if e.type == VIDEORESIZE]
        if resize_events:
            self.update_layout((resize_events[-1].w,resize_events[-1].h))
        self.menu_bar.handle_events(events)
        self.camera_view.handle_events(events)
        self.control_panel.handle_events(events)
        self.file_viewer.handle_events(events)
        current_selected = self.file_viewer.get_selected_files()
        if current_selected != self._prev_file_selection and len(current_selected) == 1:
            self.load_selected_image()
        self._prev_file_selection = current_selected
        return

    def update(self):
        self.file_viewer.update()
        self.camera_view.update()
        if self.camera_thread and self.camera_thread.is_running:
            frame = self.camera_thread.get_frame()
            if frame is not None:
                self.live_frame = frame
                self.camera_view.set_live_frame(frame)
            if self.camera_view.viewing_mode == "live":
                hist = self.camera_thread.get_histogram()
                if hist is not None:
                    self.histogram_view.hist = hist
                    try:
                        if self.live_frame:
                            frame_array = surfarray.array3d(self.live_frame)
                            self.control_panel.set_indicator_status(frame_array)
                    except Exception as e:
                        print(f"Eror updating indicator: {e}")
        return
    
    def draw(self,screen):
        self.menu_bar.draw(screen)
        self.camera_view.draw(screen)
        self.histogram_view.draw(screen)
        self.control_panel.draw(screen)
        self.file_viewer.draw(screen)
        return

    def setup_menu_bar(self):
        self.menu_bar = MenuBar(
            scene_instance=self,
            scene = "image_acquisition",
            rel_pos = (0.0,0.0),
            rel_size = (1.0,0.05),
            switch_scene_callback=self.switch_scene_callback,
            call_methodes=[self._load_images,self._save_images],
            reference_resolution=self.settings.saved_settings["display"]["resolution"]
        )

    def setup_camera_view(self):
        """Setup the camera view window"""
        self.camera_view = CameraView(
            rel_pos=(0.001, 0.051),
            rel_size=(0.659, 0.609),
            reference_resolution=self.settings.saved_settings["resolution"],
            background_color=(0, 0, 0),
            border_color=(255, 0, 0)
        )
        return
    
    def setup_histogram_view(self):
        """Setup the histogram view window"""
        self.histogram_view = HistogramView(
            rel_pos=(0.331, 0.661),
            rel_size=(0.329, 0.339),
            reference_resolution=self.settings.saved_settings["resolution"],
            background_color=(0, 0, 0),
            border_color=(255, 0, 0)
        )
        return
    
    def setup_control_panel(self):
        """Setup the control panel"""
        self.control_panel = ControlPanel(
            rel_pos=(0.001, 0.661),
            rel_size=(0.329, 0.339),
            reference_resolution=self.settings.saved_settings["resolution"],
            on_capture=lambda: self.capture_image(),
            on_rotate=lambda: self.rotate_view(),
            on_homing=lambda: self.homing_position(),
            on_calibrate=lambda: self.calibrate_position(),
            on_live=lambda: self.live_image()
        )
        return

    def setup_file_viewer(self):
        self.file_viewer = FileViewer(
            rel_pos=(0.661, 0.051),
            rel_size=(0.338, 0.948),
            reference_resolution=self.settings.saved_settings["resolution"],
            background_color=self.settings.saved_settings.get("backgroundcolor", [30, 30, 30]),
            folder_color=(100, 150, 200),
            file_color=(200, 200, 200),
            selected_color=(80, 120, 160),
            hover_color=(60, 60, 80),
            text_color=(255, 255, 255)
        )
        return
    
    def setup_working_directory(self):
        self.working_dir = Path.cwd() / "working_directory"
        if not self.working_dir.exists():
            self.working_dir.mkdir(parents=True)
            print(f"Working directory created: {self.working_dir}")
        self.file_viewer.load_directory(str(self.working_dir))
        return
    
    def init_camera(self)->None:
        try:
            self.camera_thread = CameraThread(histogram_interval=3)
            if not self.camera_thread.start():
                print(f"Failed to start camera: {self.camera_thread.last_error}")
                self.camera_thread = None
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera_thread = None
        return
    
    def switch_scene(self,call):
        if self.camera_thread and self.camera_thread.is_running:
            self.camera_thread.stop()
            self.camera_thread = None
        self.switch_scene_callback(call)
        return
    
    def on_scene_enter(self):
        if self.camera_view.viewing_mode == "live" and (self.camera_thread is None or not self.camera_thread.is_running):
            self.init_camera()
        return
        
    def capture_image(self):
        if self.live_frame is None:
            print("No camera feed available to capture")
            return
        try:
            if not self.working_dir.exists():
                self.working_dir.mkdir(parents=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.png"
            filepath = self.working_dir / filename
            image.save(self.live_frame, str(filepath))
            print(f"Image captured: {filepath}")
            self.file_viewer.load_directory(str(self.working_dir))
        except Exception as e:
            print(f"Error capturing image: {e}")
        return

    def live_image(self):
        self.camera_view.switch_to_live()
        if self.camera_thread is None or not self.camera_thread.is_running:
            self.init_camera()
        return

    def rotate_view(self):
        self.camera_view.rotate_view()
        return

    def homing_position(self):
        pass

    def calibrate_position(self):
        pass
    
    def load_selected_image(self):
        selected_files = self.file_viewer.get_selected_files()
        if not selected_files:
            print("No image selected")
            return
        try:
            image_path = selected_files[0]
            loaded_image = image.load(str(image_path))
            self.camera_view.set_selected_image(loaded_image)
            if self.camera_thread and self.camera_thread.is_running:
                self.camera_thread.stop()
                self.camera_thread = None
            frame_array = surfarray.array3d(loaded_image)
            hist = self.histogram_view.calculate_histogram(frame_array)
            if hist is not None:
                self.histogram_view.hist = hist
                self.control_panel.set_indicator_status(frame_array)
            print(f"Loaded image: {image_path.name}")
        except Exception as e:
            print(f"Error loading image: {e}")
        return
    
    def _load_images(self)->None:
        try:
            root = Tk()
            root.withdraw()
            working_dir = self.scene_instance.working_dir
            initial_dir = str(working_dir) if working_dir.exists() else None
            filepaths = filedialog.askopenfilenames(
                title="Select Images to Load",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                    ("All files", "*.*")
                ],
                initialdir=initial_dir
            )
            root.destroy()
            if not filepaths:
                return
            working_dir = self.scene_instance.working_dir
            if not working_dir.exists():
                working_dir.mkdir(parents=True)
            count = 0
            for filepath in filepaths:
                source_file = Path(filepath)
                copy2(source_file, working_dir / source_file.name)
                count += 1
            if count > 0:
                print(f"Loaded {count} images")
                self.scene_instance.file_viewer.load_directory(str(working_dir))
        except Exception as e:
            print(f"Error loading images: {e}")
        return

    def _save_images(self):
        try:
            working_dir = self.scene_instance.working_dir
            if not working_dir.exists() or not any(working_dir.iterdir()):
                print("No images to save")
                return
            root = Tk()
            root.withdraw()
            initial_dir = str(working_dir.parent) if working_dir.exists() else None
            filepath = filedialog.asksaveasfilename(
                title="Save Images As (will add numbers)",
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
                initialdir=initial_dir,
                initialfile="image_001.png"
            )
            root.destroy()
            if filepath:
                save_path = Path(filepath).parent
                base_name = Path(filepath).stem
                extension = Path(filepath).suffix
                count = 0
                for i, file in enumerate(working_dir.iterdir()):
                    if file.is_file():
                        new_filename = f"{base_name}_{i:03d}{extension}"
                        copy2(file, save_path / new_filename)
                        count += 1
                print(f"Saved {count} images to: {save_path}")
        except Exception as e:
            print(f"Error saving images: {e}")
        return
    
    def cleanup(self):
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread = None
        if hasattr(self, 'working_dir') and self.working_dir.exists():
            try:
                rmtree(self.working_dir)
                print(f"Working directory deleted: {self.working_dir}")
            except Exception as e:
                print(f"Error deleting working directory: {e}")
        return
    
    def __del__(self):
        self.cleanup()