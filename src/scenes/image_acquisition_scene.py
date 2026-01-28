from pygame import VIDEORESIZE, surfarray, image
from pathlib import Path
from shutil import rmtree, copy2
from datetime import datetime
from tkinter import Tk, filedialog
from windows.file_viewer import FileViewer
from windows.menu_bar import MenuBar
from windows.camera_view import CameraView
from windows.control_panel import ControlPanel
from windows.histogram_view import HistogramView
from camera import CameraThread
from stage_control import StageController
from typing import Tuple, List

class ImageAcquisitionScene:
    def __init__(self, screen, settings, switch_scene_callback):
        """
        Initialize the Image Acquisition Scene
        
        Args:
            screen: Pygame display surface
            settings: Settings instance
            switch_scene_callback: Callback to switch between scenes
        """
        self.settings = settings
        self.switch_scene_callback = switch_scene_callback
        self.live_frame = None
        self.camera_thread = None
        self._prev_file_selection = []
        self.setup_working_directory()
        self.setup_stage_control()
        self.setup_menu_bar()
        self.setup_camera_view()
        self.setup_histogram_view()
        self.setup_control_panel()
        self.setup_file_viewer()
        self.init_camera()
        self.update_layout(screen.get_size())
        return
    
    def setup_working_directory(self):
        """Setup working directory for temporary images"""
        self.working_dir = Path.cwd() / "working_directory"
        if not self.working_dir.exists():
            self.working_dir.mkdir(parents=True)
            print(f"Working directory created: {self.working_dir}")
        return
    
    def setup_stage_control(self):
        """Setup stage controller for motor control"""
        try:
            self.stage_control = StageController(
                settings=self.settings,
                on_move_complete=self._on_stage_move_complete
            )
            if self.stage_control.initialized:
                print("Stage control initialized successfully")
        except Exception as e:
            print(f"Error initializing stage control: {e}")
            self.stage_control = None
        return
    
    def setup_menu_bar(self):
        """Setup the menu bar"""
        self.menu_bar = MenuBar(
            scene_instance=self,
            scene="image_acquisition",
            rel_pos=(0.0, 0.0),
            rel_size=(1.0, 0.05),
            switch_scene_callback=self.switch_scene_callback,
            call_methodes=[self._load_images, self._save_images],
            reference_resolution=self.settings.saved_settings["display"]["resolution"]
        )
        return
    
    def setup_camera_view(self):
        """Setup the camera view window"""
        self.camera_view = CameraView(
            rel_pos=(0.001, 0.051),
            rel_size=(0.659, 0.609),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(0, 0, 0),
            border_color=(255, 0, 0),
            on_mode_change_callback=self._on_camera_view_mode_changed
        )
        return
    
    def setup_histogram_view(self):
        """Setup the histogram view window"""
        self.histogram_view = HistogramView(
            rel_pos=(0.331, 0.661),
            rel_size=(0.329, 0.339),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(0, 0, 0),
            border_color=(255, 0, 0)
        )
        return
    
    def setup_control_panel(self):
        """Setup the control panel"""
        self.control_panel = ControlPanel(
            rel_pos=(0.001, 0.661),
            rel_size=(0.329, 0.339),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            stage_control=self.stage_control,
            on_capture=lambda: self.capture_image(),
            on_rotate=lambda: self.rotate_view(),
            on_live=lambda: self.live_image()
        )
        return
    
    def setup_file_viewer(self):
        """Setup the file viewer"""
        self.file_viewer = FileViewer(
            rel_pos=(0.661, 0.051),
            rel_size=(0.338, 0.948),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            folder_color=(100, 150, 200),
            file_color=(200, 200, 200),
            selected_color=(80, 120, 160),
            hover_color=(60, 60, 80),
            text_color=(255, 255, 255)
        )
        self.file_viewer.load_directory(str(self.working_dir))
        return
    
    def init_camera(self):
        """Initialize camera thread"""
        try:
            self.camera_thread = CameraThread()
            if not self.camera_thread.start():
                print(f"Failed to start camera: {self.camera_thread.last_error}")
                self.camera_thread = None
        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.camera_thread = None
        return
    
    def update_layout(self, window_size: Tuple[int, int]):
        """
        Update layout when window is resized
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        self.menu_bar.update_layout(window_size)
        self.camera_view.update_layout(window_size)
        self.histogram_view.update_layout(window_size)
        self.control_panel.update_layout(window_size)
        self.file_viewer.update_layout(window_size)
        return

    def handle_events(self, events: list):
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
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
        """Update scene state (called every frame)"""
        self.file_viewer.update()
        self.camera_view.update()
        if not self.camera_view.is_live_view:
            return
        if not self.camera_thread or not self.camera_thread.is_running:
            return
        frame = self.camera_thread.get_frame()
        if frame is None:
            return
        self.live_frame = frame
        self.camera_view.set_live_frame(frame)
        self.histogram_view.update_from_frame(frame)
        try:
            frame_array = surfarray.array3d(frame)
            self.control_panel.set_image_indicator_status(frame_array)
        except Exception as e:
            print(f"Error updating indicator: {e}")
        return
    
    def draw(self,screen):
        """
        Draw the scene
        
        Args:
            screen: Pygame surface to draw on
        """
        self.menu_bar.draw(screen)
        self.camera_view.draw(screen)
        self.histogram_view.draw(screen)
        self.control_panel.draw(screen)
        self.file_viewer.draw(screen)
        return
    
    def _on_camera_view_mode_changed(self, is_live: bool):
        """
        Called when camera view switches between live and image mode
        
        Args:
            is_live: True if switched to live mode, False if switched to image mode
        """
        if is_live:
            if self.camera_thread and self.camera_thread.is_running:
                self.camera_thread.resume()
        else:
            if self.camera_thread and self.camera_thread.is_running:
                self.camera_thread.pause()
        return
    
    def _on_stage_move_complete(self):
        """Called when stage movement completes"""
        self.control_panel.update_position_display()
        return
    
    def capture_image(self):
        """Capture current live frame and save to working directory"""
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
        """Switch to live camera view"""
        self.camera_view.switch_to_live()
        if self.camera_thread is None or not self.camera_thread.is_running:
            self.init_camera()
        return
    
    def rotate_view(self):
        """Rotate the camera view by 90 degrees"""
        self.camera_view.rotate_view()
        return
    
    def load_selected_image(self):
        """Load and display the selected image from file viewer"""
        selected_files = self.file_viewer.get_selected_files()
        if not selected_files:
            print("No image selected")
            return
        try:
            image_path = selected_files[0]
            loaded_image = image.load(str(image_path))
            self.camera_view.set_selected_image(loaded_image)
            frame_array = surfarray.array3d(loaded_image)
            self.histogram_view.force_update(frame_array)
            self.control_panel.set_image_indicator_status(frame_array)
            print(f"Loaded image: {image_path.name}")
        except Exception as e:
            print(f"Error loading image: {e}")
        return
    
    def _load_images(self):
        """Load images from file system into working directory"""
        try:
            root = Tk()
            root.withdraw()
            initial_dir = str(self.working_dir) if self.working_dir.exists() else None
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
            if not self.working_dir.exists():
                self.working_dir.mkdir(parents=True)
            count = 0
            for filepath in filepaths:
                source_file = Path(filepath)
                destination = self.working_dir / source_file.name
                copy2(source_file, destination)
                count += 1
            if count > 0:
                print(f"Loaded {count} images")
                self.file_viewer.load_directory(str(self.working_dir))
        except Exception as e:
            print(f"Error loading images: {e}")
        return
    
    def _save_images(self):
        """Save images from working directory to settings save path"""
        try:
            if not self.working_dir.exists() or not any(self.working_dir.iterdir()):
                print("No images to save")
                return
            save_path = Path(self.settings.saved_settings["processing"]["save_path"])
            if not save_path.exists():
                save_path.mkdir(parents=True)
                print(f"Created save directory: {save_path}")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_dir = save_path / f"images_{timestamp}"
            save_dir.mkdir(exist_ok=True)
            count = 0
            for file in self.working_dir.iterdir():
                if file.is_file() and file.suffix.lower() in self.file_viewer.IMAGE_EXTENSIONS:
                    destination = save_dir / file.name
                    copy2(file, destination)
                    count += 1
            if count > 0:
                print(f"Saved {count} images to: {save_dir}")
            else:
                print("No images found to save")
        except Exception as e:
            print(f"Error saving images: {e}")
        return
    
    def on_scene_enter(self):
        """Called when this scene becomes active"""
        if self.camera_view.is_live_view and (self.camera_thread is None or not self.camera_thread.is_running):
            self.init_camera()
        return
    
    def cleanup(self):
        """Cleanup scene resources"""
        if self.camera_thread and self.camera_thread.is_running:
            self.camera_thread.stop()
            self.camera_thread = None
            print("Camera thread stopped")
        if self.stage_control and self.stage_control.initialized:
            self.stage_control.cleanup()
            print("Stage control cleaned up")
        if hasattr(self, 'working_dir') and self.working_dir.exists():
            try:
                rmtree(self.working_dir)
                print(f"Working directory deleted: {self.working_dir}")
            except Exception as e:
                print(f"Error deleting working directory: {e}")
        return