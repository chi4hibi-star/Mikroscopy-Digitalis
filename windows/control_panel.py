from windows.base_window import BaseWindow
from UI.grid import Grid
from UI.button import Button
from UI.indicator import Indicator
from UI.label import Label
from UI.inputfield import InputField

class ControlPanel(BaseWindow):
    def __init__(
                self,
                rel_pos=(0.001, 0.661),
                rel_size=(0.329, 0.339),
                reference_resolution=(1920, 1080),
                on_capture=None,
                on_rotate=None,
                on_homing=None,
                on_calibrate=None,
                on_live=None
                ):
        """
        Initialize the ControlPanel
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
            on_capture: Callback for capture button
            on_rotate: Callback for rotate button
            on_homing: Callback for homing button
            on_calibrate: Callback for calibrate button
            on_live: Callback for live button
            on_zoom: Callback for zoom button (takes zoom amount as parameter)
            on_zoom_home: Callback for zoom home button
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.on_capture = on_capture or (lambda: None)
        self.on_rotate = on_rotate or (lambda: None)
        self.on_homing = on_homing or (lambda: None)
        self.on_calibrate = on_calibrate or (lambda: None)
        self.on_live = on_live or (lambda: None)
        self.grid = Grid(
            rel_pos=rel_pos,
            rel_size=rel_size,
            rows=3,
            cols=5,
            reference_resolution=reference_resolution
        )
        self._create_ui_elements()
        return
    
    def _create_ui_elements(self):
        """Create all UI elements for the control panel"""
        res = self.reference_resolution
        self.capture_button = Button(
            text="Capture",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self.on_capture,
            reference_resolution=res
        )
        self.rotate_button = Button(
            text="Rotate",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self.on_rotate,
            reference_resolution=res
        )
        self.homing_button = Button(
            text="Homing",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self.on_homing,
            reference_resolution=res
        )
        self.calibrate_button = Button(
            text="Calibrate",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self.on_calibrate,
            reference_resolution=res
        )
        self.live_button = Button(
            text="Live",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self.on_live,
            reference_resolution=res
        )
        self.indicator = Indicator(
            rel_pos=(0, 0),
            rel_size=(0.05, 0.05),
            status="red",
            reference_resolution=res
        )
        self.xpos_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="X: 0.00",
            reference_resolution=res
        )
        self.ypos_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Y: 0.00",
            reference_resolution=res
        )
        self.zpos_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Z: 0.00",
            reference_resolution=res
        )
        self.xpos_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            input_type="numbers",
            start_text="0.00",
            reference_resolution=res
        )
        self.ypos_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            input_type="numbers",
            start_text="0.00",
            reference_resolution=res
        )
        self.zpos_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            input_type="numbers",
            start_text="0.00",
            reference_resolution=res
        )
        # Row 0
        self.grid.add_object(self.capture_button, 0, 0, "center")
        self.grid.add_object(self.xpos_label, 0, 1, "center")
        self.grid.add_object(self.xpos_input, 0, 2, "center")
        self.grid.add_object(self.homing_button, 0, 3, "center")
        
        # Row 1
        self.grid.add_object(self.indicator, 1, 0, "center")
        self.grid.add_object(self.ypos_label, 1, 1, "center")
        self.grid.add_object(self.ypos_input, 1, 2, "center")
        self.grid.add_object(self.calibrate_button, 1, 3, "center")
        
        # Row 2
        self.grid.add_object(self.rotate_button, 2, 0, "center")
        self.grid.add_object(self.zpos_label, 2, 1, "center")
        self.grid.add_object(self.zpos_input, 2, 2, "center")
        self.grid.add_object(self.live_button, 2, 3, "center")
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
        """Draw control panel"""
        self.grid.draw(surface)
        return
    
    def set_indicator_status(self, frame_array):
        """
        Update the indicator status based on frame
        
        Args:
            frame_array: Numpy array of the frame
        """
        self.indicator.set_status(frame_array)
        return
    
    def set_position(self, x, y, z):
        """
        Update position labels and inputs
        
        Args:
            x: X position
            y: Y position
            z: Z position
        """
        self.xpos_label.set_text(f"X: {x:.2f}")
        self.ypos_label.set_text(f"Y: {y:.2f}")
        self.zpos_label.set_text(f"Z: {z:.2f}")
        self.xpos_input.text = f"{x:.2f}"
        self.ypos_input.text = f"{y:.2f}"
        self.zpos_input.text = f"{z:.2f}"
        return
    
    def get_position(self):
        """
        Get position values from input fields
        
        Returns:
            Tuple of (x, y, z) as floats
        """
        try:
            x = float(self.xpos_input.text) if self.xpos_input.text else 0.0
            y = float(self.ypos_input.text) if self.ypos_input.text else 0.0
            z = float(self.zpos_input.text) if self.zpos_input.text else 0.0
            return (x, y, z)
        except ValueError:
            return (0.0, 0.0, 0.0)