from UI.button import Button
from UI.grid import Grid
from UI.label import Label
from UI.dropdownmenu import DropdownMenu
from windows.base_window import BaseWindow

class ProcessingControlPanel(BaseWindow):
    """Control panel for processing operations"""
    def __init__(self,
                 settings,
                 rel_pos=(0.251, 0.661),
                 rel_size=(0.498, 0.338),
                 reference_resolution=(1920, 1080),
                 on_process=None,
                 on_output_mode_change=None,
                 on_set_view_mode=None):
        super().__init__(rel_pos,rel_size,reference_resolution)
        self.settings = settings
        self.on_process = on_process or (lambda: None)
        self.on_output_mode_change = on_output_mode_change or (lambda x: None)
        self.on_set_view_mode = on_set_view_mode or (lambda x: None)
        grid_padding_vertical = 0.05
        grid_padding_herizontal = 0.03
        grid_rel_pos = (
            rel_pos[0] + (rel_size[0] * grid_padding_herizontal),
            rel_pos[1] + (rel_size[1] * grid_padding_vertical)
        )
        grid_rel_size = (
            rel_size[0] * (1 - 2 * grid_padding_herizontal),
            rel_size[1] * (1 - 2 * grid_padding_vertical)
        )
        self.grid = Grid(
            rel_pos=grid_rel_pos,
            rel_size=grid_rel_size,
            rows=3,
            cols=4,
            cell_padding=0.15,
            reference_resolution=reference_resolution
        )
        self._create_ui_elements()
        self.processing = False
        self.progress = 0
        self.total_images = 0
        return
    
    def _create_ui_elements(self):
        """Create control panel UI elements"""
        res = self.reference_resolution
        modes = ["Pipeline", "Input", "Output", "Compare"]
        mode_values = ["pipeline", "input", "output", "compare"]
        for i, (mode_text, mode_val) in enumerate(zip(modes, mode_values)):
            button = Button(
                text=mode_text,
                rel_pos=(0, 0),
                rel_size=(0.1, 0.05),
                callback=lambda m=mode_val: self.on_set_view_mode(m),
                reference_resolution=res
            )
            self.grid.add_object(button,0,i,"center")
        self.process_button = Button(
            text="Process Image",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=self.on_process,
            base_color=(70, 200, 70),
            hover_color=(100, 240, 100),
            reference_resolution=res
        )
        output_modes = ["Data Only", "Images Only", "Full Documentation"]
        default_mode = self.settings.saved_settings.get("output_mode", "Images Only")
        default_index = output_modes.index(default_mode) if default_mode in output_modes else 1
        self.output_mode_dropdown = DropdownMenu(
            rel_pos=(0, 0),
            rel_size=(0.12, 0.03),
            options=output_modes,
            selected_index=default_index,
            reference_resolution=res
        )
        self.progress_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Ready",
            reference_resolution=res
        )
        self.grid.add_object(self.process_button, 1, 0, "center")
        self.grid.add_object(self.progress_label, 1, 1, "center")
        self.grid.add_object(self.output_mode_dropdown, 1, 3, "center")
        return
    
    def update_layout(self, window_size):
        """Update control panel layout"""
        super().update_layout(window_size)
        self.grid.update_layout(window_size)
        return
    
    def handle_events(self, events):
        """Handle events"""
        self.handle_resize_events(events)
        self.grid.handle_events(events)
        current_mode = self.output_mode_dropdown.get_selected()
        if current_mode != self.settings.saved_settings.get("output_mode"):
            self.on_output_mode_change(current_mode)
        return
    
    def update(self):
        """Update control panel state"""
        self.grid.update()
        return
    
    def draw(self, surface):
        """Draw control panel"""
        self.grid.draw(surface)
        return
    
    def set_image_count(self, count):
        """Update process button text based on image count"""
        if count == 0:
            self.process_button.set_text("No Images")
            self.process_button.set_enabled(False)
        elif count == 1:
            self.process_button.set_text("Process Image")
            self.process_button.set_enabled(True)
        else:
            self.process_button.set_text(f"Process {count} Images")
            self.process_button.set_enabled(True)
        return
    
    def set_processing(self, active, progress=0, total=0):
        """Set processing state and progress"""
        self.processing = active
        self.progress = progress
        self.total_images = total
        
        if active:
            self.process_button.set_enabled(False)
            if total > 1:
                self.progress_label.set_text(f"Processing {progress}/{total}...")
            else:
                self.progress_label.set_text("Processing...")
        else:
            self.process_button.set_enabled(True)
            self.progress_label.set_text("Ready")
        return