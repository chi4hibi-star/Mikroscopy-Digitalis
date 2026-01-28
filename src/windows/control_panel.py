from windows.base_window import BaseWindow
from UI.grid import Grid
from UI.button import Button
from UI.indicator import Indicator
from UI.label import Label
from UI.inputfield import InputField
from typing import Optional, Callable

class ControlPanel(BaseWindow):
    def __init__(
                self,
                rel_pos=(0.001, 0.661),
                rel_size=(0.329, 0.339),
                reference_resolution=(1920, 1080),
                stage_control=None,
                on_capture: Optional[Callable] = None,
                on_rotate: Optional[Callable] = None,
                on_live: Optional[Callable] = None
                ):
        """
        Initialize the ControlPanel
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
            stage_control: StageController instance (optional)
            on_capture: Callback for capture button
            on_rotate: Callback for rotate button
            on_live: Callback for live button
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.stage_control = stage_control
        self.on_capture = on_capture or (lambda: None)
        self.on_rotate = on_rotate or (lambda: None)
        self.on_live = on_live or (lambda: None)
        self.grid = Grid(
            rel_pos=rel_pos,
            rel_size=rel_size,
            rows=6,
            cols=4,
            cell_padding=0.05,
            reference_resolution=reference_resolution
        )
        self._create_ui_elements()
        return
    
    def _create_ui_elements(self):
        """Create all UI elements for the control panel"""
        res = self.reference_resolution
        # ========== SECTION 1: CAMERA CONTROLS (Row 0) ==========
        self.camera_section_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Camera Controls",
            text_color=(200, 200, 200),
            text_style="bold",
            reference_resolution=res
        )
        self.grid.add_object(self.camera_section_label, 0, 0, align="left")
        # Row 1: Camera buttons
        self.live_button = Button(
            text="Live",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self.on_live,
            reference_resolution=res
        )
        self.grid.add_object(self.live_button, 1, 0, align="center")
        self.capture_button = Button(
            text="Capture",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self.on_capture,
            reference_resolution=res
        )
        self.grid.add_object(self.capture_button, 1, 1, align="center")
        self.rotate_button = Button(
            text="Rotate",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self.on_rotate,
            reference_resolution=res
        )
        self.grid.add_object(self.rotate_button, 1, 2, align="center")
        # ========== SECTION 2: STAGE CONTROLS (Rows 2-4) ==========
        self.stage_section_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Stage Controls",
            text_color=(200, 200, 200),
            text_style="bold",
            reference_resolution=res
        )
        self.grid.add_object(self.stage_section_label, 2, 0, align="left")
        # Row 3: Position inputs
        self.x_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.05, 0.05),
            text="X:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        self.grid.add_object(self.x_label, 3, 0, align="right")
        self.x_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            input_type="numbers",
            start_text="0.00",
            reference_resolution=res
        )
        self.grid.add_object(self.x_input, 3, 1, align="center")
        self.y_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.05, 0.05),
            text="Y:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        self.grid.add_object(self.y_label, 3, 2, align="right")
        self.y_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            input_type="numbers",
            start_text="0.00",
            reference_resolution=res
        )
        self.grid.add_object(self.y_input, 3, 3, align="center")
        # Row 4: Z input and Move button
        self.z_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.05, 0.05),
            text="Z:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        self.grid.add_object(self.z_label, 4, 0, align="right")
        self.z_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            input_type="numbers",
            start_text="0.00",
            reference_resolution=res
        )
        self.grid.add_object(self.z_input, 4, 1, align="center")
        self.move_button = Button(
            text="Move To",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self._on_move_to,
            base_color=(70, 150, 70),
            hover_color=(100, 180, 100),
            reference_resolution=res
        )
        self.grid.add_object(self.move_button, 4, 2, align="center")
        self.stop_button = Button(
            text="STOP",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self._on_stop,
            base_color=(200, 50, 50),
            hover_color=(240, 80, 80),
            reference_resolution=res
        )
        self.grid.add_object(self.stop_button, 4, 3, align="center")
        # ========== SECTION 3: STAGE SETUP (Row 5 left side) ==========
        self.home_button = Button(
            text="Home",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self._on_home,
            reference_resolution=res
        )
        self.grid.add_object(self.home_button, 5, 0, align="center")
        self.calibrate_button = Button(
            text="Calibrate",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self._on_calibrate,
            reference_resolution=res
        )
        self.grid.add_object(self.calibrate_button, 5, 1, align="center")
        # ========== SECTION 4: STATUS INDICATORS (Right side) ==========
        self.image_indicator_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Image:",
            text_color=(200, 200, 200),
            reference_resolution=res
        )
        self.grid.add_object(self.image_indicator_label, 0, 3, align="center")
        self.image_indicator = Indicator(
            rel_pos=(0, 0),
            rel_size=(0.05, 0.05),
            status="red",
            reference_resolution=res
        )
        self.grid.add_object(self.image_indicator, 1, 3, align="center")
        self.stage_indicator_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Stage:",
            text_color=(200, 200, 200),
            reference_resolution=res
        )
        self.grid.add_object(self.stage_indicator_label, 2, 3, align="center")
        self.stage_status_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Not Init",
            text_color=(150, 150, 150),
            reference_resolution=res
        )
        self.grid.add_object(self.stage_status_label, 3, 3, align="center")
        self._update_stage_controls()
        return
    
    def update_layout(self, window_size):
        """
        Update control panel size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        super().update_layout(window_size)
        self.grid.update_layout(window_size)
        return
    
    def handle_events(self, events):
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_events(events)
        self.grid.handle_events(events)
        return
    
    def update(self):
        """Update the control panel state (called every frame)"""
        self.grid.update()
        return
    
    def draw(self, surface):
        """
        Draw control panel
        
        Args:
            surface: Pygame surface to draw on
        """
        self.grid.draw(surface)
        return
    
    def _update_stage_controls(self):
        """Enable/disable stage controls based on stage availability"""
        stage_available = self.stage_control is not None and self.stage_control.initialized
        self.move_button.set_enabled(stage_available)
        self.home_button.set_enabled(stage_available)
        self.calibrate_button.set_enabled(stage_available)
        self.stop_button.set_enabled(stage_available)
        self.x_input.set_enabled(stage_available) if hasattr(self.x_input, 'set_enabled') else None
        self.y_input.set_enabled(stage_available) if hasattr(self.y_input, 'set_enabled') else None
        self.z_input.set_enabled(stage_available) if hasattr(self.z_input, 'set_enabled') else None
        if stage_available:
            self.stage_status_label.set_text("Idle")
            self.stage_status_label.set_text_color((100, 255, 100))
        else:
            self.stage_status_label.set_text("Not Init")
            self.stage_status_label.set_text_color((150, 150, 150))
        return
    
    def _on_move_to(self):
        """Handle Move To button press"""
        if not self.stage_control or not self.stage_control.initialized:
            print("Stage not initialized")
            return
        if self.stage_control.is_moving:
            print("Stage already moving")
            return
        try:
            x = float(self.x_input.get_text()) if self.x_input.get_text() else 0.0
            y = float(self.y_input.get_text()) if self.y_input.get_text() else 0.0
            z = float(self.z_input.get_text()) if self.z_input.get_text() else 0.0
            self.stage_status_label.set_text("Moving...")
            self.stage_status_label.set_text_color((255, 200, 100))
            self.stage_control.move_to(x=x, y=y, z=z, wait=False)
        except ValueError:
            print("Invalid position values")
        return
    
    def _on_home(self):
        """Handle Home button press"""
        if not self.stage_control or not self.stage_control.initialized:
            print("Stage not initialized")
            return
        if self.stage_control.is_moving:
            print("Stage already moving")
            return
        self.stage_status_label.set_text("Homing...")
        self.stage_status_label.set_text_color((255, 200, 100))
        self.stage_control.home(wait=False)
        return
    
    def _on_calibrate(self):
        """Handle Calibrate button press"""
        if not self.stage_control or not self.stage_control.initialized:
            print("Stage not initialized")
            return
        if self.stage_control.is_moving:
            print("Stage already moving")
            return
        self.stage_status_label.set_text("Calibrating...")
        self.stage_status_label.set_text_color((255, 200, 100))
        self.stage_control.calibrate(wait=False)
        return
    
    def _on_stop(self):
        """Handle Stop button press"""
        if not self.stage_control or not self.stage_control.initialized:
            return
        self.stage_control.stop()
        self.stage_status_label.set_text("Stopped")
        self.stage_status_label.set_text_color((255, 100, 100))
        return
    
    def update_position_display(self):
        """Update position display from stage (call when movement completes)"""
        if not self.stage_control or not self.stage_control.initialized:
            return
        x, y, z = self.stage_control.get_position()
        self.x_input.set_text(f"{x:.2f}")
        self.y_input.set_text(f"{y:.2f}")
        self.z_input.set_text(f"{z:.2f}")
        self.stage_status_label.set_text("Idle")
        self.stage_status_label.set_text_color((100, 255, 100))
        return
    
    def set_image_indicator_status(self, frame_array):
        """
        Update the image quality indicator status based on frame
        
        Args:
            frame_array: Numpy array of the frame
        """
        self.image_indicator.set_status(frame_array)
        return
    
    def set_stage_control(self, stage_control):
        """
        Set or update the stage control reference
        
        Args:
            stage_control: StageController instance
        """
        self.stage_control = stage_control
        self._update_stage_controls()
        return