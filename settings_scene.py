from pygame import VIDEORESIZE
from windows.menu_bar import MenuBar
from UI.grid import Grid
from UI.label import Label
from UI.dropdownmenu import DropdownMenu

class SettingsScene:
    def __init__(self, screen, settings, switch_scene_callback, save_settings_callback):
        """
        Initialize the Settings Scene
        
        Args:
            screen: Pygame display surface
            settings: Settings instance
            switch_scene_callback: Function to switch between scenes
        """
        self.settings = settings
        self.switch_scene_callback = switch_scene_callback
        window_width, window_height = screen.get_size()
        self.current_window_size = (window_width, window_height)
        self.save_settings_callback = save_settings_callback

        self.setup_menu_bar()
        self.setup_settings_panel()
        self.update_layout(window_width, window_height)
        
        self.pending_resolution = self.settings.saved_settings.get("resolution", [1920, 1080])
        self.pending_display_flag = self.settings.saved_settings.get("display_flag", "RESIZABLE")
        self.pending_language = self.settings.saved_settings.get("language", "English")
        self.pending_camera = self.settings.saved_settings.get("camera", "Daheng")
        return
    
    def setup_menu_bar(self):
        """Setup the menu bar"""
        self.menu_bar = MenuBar(
            scene_instance=self,
            scene="settings",
            rel_pos=(0.0, 0.0),
            rel_size=(1.0, 0.05),
            switch_scene_callback=self.switch_scene_callback,
            save_settings_callback = self.save_settings_callback,
            reference_resolution=self.settings.saved_settings["resolution"]
        )
        return
    
    def setup_settings_panel(self):
        """Setup the settings panel with all controls"""
        self.main_grid = Grid(
            rel_pos=(0.1, 0.15),
            rel_size=(0.8, 0.7),
            rows=5,
            cols=2,
            cell_padding=0.15,
            reference_resolution=self.settings.saved_settings["resolution"]
        )
        res = self.settings.saved_settings["resolution"]
        resolution_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Resolution:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        resolution_options = [
            "1920x1080",
            "1600x900",
            "1366x768",
            "1280x720",
            "1024x768"
        ]
        current_res = f"{self.settings.saved_settings['resolution'][0]}x{self.settings.saved_settings['resolution'][1]}"
        current_res_idx = resolution_options.index(current_res) if current_res in resolution_options else 0
        
        self.resolution_dropdown = DropdownMenu(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            options=resolution_options,
            selected_index=current_res_idx,
            reference_resolution=res
        )
        display_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Display Mode:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        display_options = ["RESIZABLE", "FULLSCREEN"]
        current_display_idx = display_options.index(self.settings.saved_settings.get("display_flag", "RESIZABLE"))
        
        self.display_dropdown = DropdownMenu(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            options=display_options,
            selected_index=current_display_idx,
            reference_resolution=res
        )
        language_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Language:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        language_options = ["English", "German", "Spanish", "French"]
        current_lang = self.settings.saved_settings.get("language", "English")
        current_lang_idx = language_options.index(current_lang) if current_lang in language_options else 0
        
        self.language_dropdown = DropdownMenu(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            options=language_options,
            selected_index=current_lang_idx,
            reference_resolution=res
        )
        camera_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Camera:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        camera_options = ["Daheng", "iDS"]
        current_camera = self.settings.saved_settings.get("camera", "Daheng")
        current_camera_idx = camera_options.index(current_camera) if current_camera in camera_options else 0
        
        self.camera_dropdown = DropdownMenu(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            options=camera_options,
            selected_index=current_camera_idx,
            reference_resolution=res
        )
        self.info_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Configure application settings",
            text_color=(180, 180, 180),
            reference_resolution=res
        )
        self.main_grid.add_object(self.info_label, 0, 0, "center")
        
        self.main_grid.add_object(resolution_label, 1, 0, "center")
        self.main_grid.add_object(self.resolution_dropdown, 1, 1, "center")
        
        self.main_grid.add_object(display_label, 2, 0, "center")
        self.main_grid.add_object(self.display_dropdown, 2, 1, "center")
        
        self.main_grid.add_object(language_label, 3, 0, "center")
        self.main_grid.add_object(self.language_dropdown, 3, 1, "center")
        
        self.main_grid.add_object(camera_label, 4, 0, "center")
        self.main_grid.add_object(self.camera_dropdown, 4, 1, "center")
        return
    
    def update_layout(self, width, height):
        """Update layout when window is resized"""
        self.current_window_size = (width, height)
        self.menu_bar.update_layout((width, height))
        self.main_grid.update_layout((width, height))
        return
    
    def handle_events(self, events):
        """Handle pygame events"""
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout(event.w, event.h)
        self.menu_bar.handle_events(events)
        self.main_grid.handle_events(events)
        return
    
    def update(self):
        """Update scene state"""
        self.main_grid.update()
        return
    
    def draw(self, screen):
        """Draw the settings scene"""
        background_color = self.settings.saved_settings.get("backgroundcolor", [30, 30, 30])
        screen.fill(background_color)
        self.menu_bar.draw(screen)
        self.main_grid.draw(screen)
        return
    
    def save_settings(self):
        """Save the current settings"""
        resolution_str = self.resolution_dropdown.get_selected()
        display_flag = self.display_dropdown.get_selected()
        language = self.language_dropdown.get_selected()
        camera = self.camera_dropdown.get_selected()
        resolution = [int(x) for x in resolution_str.split('x')]
        new_settings = (
            resolution,
            display_flag,
            language,
            camera
        )
        self.settings.save_settings(new_settings)
        return
    
    def cancel_settings(self):
        """Cancel and return to previous scene"""
        self.switch_scene_callback("image_acquisition")
        return
    
    def on_scene_enter(self):
        """Called when this scene becomes active"""
        resolution_str = f"{self.settings.saved_settings['resolution'][0]}x{self.settings.saved_settings['resolution'][1]}"
        resolution_options = self.resolution_dropdown.options
        if resolution_str in resolution_options:
            self.resolution_dropdown.set_selected_index(resolution_options.index(resolution_str))
        
        display_options = self.display_dropdown.options
        display_flag = self.settings.saved_settings.get("display_flag", "RESIZABLE")
        if display_flag in display_options:
            self.display_dropdown.set_selected_index(display_options.index(display_flag))
        
        language_options = self.language_dropdown.options
        language = self.settings.saved_settings.get("language", "English")
        if language in language_options:
            self.language_dropdown.set_selected_index(language_options.index(language))
        
        camera_options = self.camera_dropdown.options
        camera = self.settings.saved_settings.get("camera", "Daheng")
        if camera in camera_options:
            self.camera_dropdown.set_selected_index(camera_options.index(camera))
        return
    
    def switch_scene(self, call):
        """Switch to a different scene"""
        self.switch_scene_callback(call)
        return
    
    def cleanup(self):
        """Cleanup scene resources"""
        pass