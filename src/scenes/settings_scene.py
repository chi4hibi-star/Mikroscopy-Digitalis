from pygame import VIDEORESIZE
from ..windows.menu_bar import MenuBar
from ..UI.grid import Grid
from ..UI.label import Label
from ..UI.dropdownmenu import DropdownMenu
from ..UI.inputfield import InputField
from ..UI.radiobuttongroup import RadioButtonGroup

class SettingsScene:
    def __init__(self,
                 screen,
                 settings,
                 switch_scene_callback,
                 save_settings_callback,
                 previous_scene="image_acquisition"):
        """
        Initialize the Settings Scene
        
        Args:
            screen: Pygame display surface
            settings: Settings instance
            switch_scene_callback:  Dict of callback functions for each category
            previous_scene: Name of the scene to return to on cancel
        """
        self.settings = settings
        self.switch_scene_callback = switch_scene_callback
        self.save_settings_callback = save_settings_callback
        self.previous_scene = previous_scene
        window_width, window_height = screen.get_size()
        self.current_window_size = (window_width, window_height)

        self.setup_menu_bar()
        self.setup_settings_panel()
        self.update_layout(window_width, window_height)
        return
    
    def setup_menu_bar(self)->None:
        """Setup the menu bar"""
        self.menu_bar = MenuBar(
            scene_instance=self,
            scene="settings",
            rel_pos=(0.0, 0.0),
            rel_size=(1.0, 0.05),
            switch_scene_callback=self.switch_scene_callback,
            call_methodes = [self.save_settings],
            reference_resolution=self.settings.saved_settings["display"]["resolution"]
        )
        return
    
    def setup_settings_panel(self)->None:
        """Setup the settings panel with all controls"""
        self.main_grid = Grid(
            rel_pos=(0.05, 0.1),
            rel_size=(0.9, 0.85),
            rows=12,
            cols=2,
            cell_padding=0.1,
            reference_resolution=self.settings.saved_settings["display"]["resolution"]
        )
        res = self.settings.saved_settings["display"]["resolution"]
        info_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Configure Application Settings",
            text_color=(180, 180, 180),
            reference_resolution=res
        )
        self.main_grid.add_object(info_label, 0, 0, align="center")
        display_mode_label = Label(
                    rel_pos=(0, 0),
                    rel_size=(0.1, 0.05),
                    text="Display Mode:",
                    text_color=(255, 255, 255),
                    reference_resolution=res
                )
        display_options = ["RESIZABLE", "FULLSCREEN", "FIXED"]
        current_display = self.settings.saved_settings["display"]["display_flag"]
        current_display_idx = display_options.index(current_display) if current_display in display_options else 0
        self.display_radio = RadioButtonGroup(
            rel_pos=(0, 0),
            rel_size=(0.4, 0.05),
            options=display_options,
            selected_index=current_display_idx,
            layout="horizontal",
            reference_resolution=res
        )
        self.main_grid.add_object(display_mode_label, 1, 0, align="left")
        self.main_grid.add_object(self.display_radio, 1, 1, align="left")
        resolution_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Resolution (ROI):",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        self.main_grid.add_object(resolution_label, 2, 0, align="left")
        current_res = self.settings.saved_settings["display"]["resolution"]
        x_label = Label(text="X:", text_color=(200, 200, 200), reference_resolution=res)
        self.resolution_x_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.04),
            input_type="numbers",
            start_text=str(current_res[0]),
            reference_resolution=res
        )
        y_label = Label(text="Y:", text_color=(200, 200, 200), reference_resolution=res)
        self.resolution_y_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.04),
            input_type="numbers",
            start_text=str(current_res[1]),
            reference_resolution=res
        )
        resolution_grid = Grid(
            rel_pos=(0, 0),
            rel_size=(0.4, 0.05),
            rows=1,
            cols=4,
            cell_padding=0.05,
            reference_resolution=res
        )
        resolution_grid.add_object(x_label, 0, 0, align="right")
        resolution_grid.add_object(self.resolution_x_input, 0, 1, align="center")
        resolution_grid.add_object(y_label, 0, 2, align="right")
        resolution_grid.add_object(self.resolution_y_input, 0, 3, align="center")
        self.main_grid.add_object(resolution_grid, 3, 1, align="left")
        fps_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="FPS:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        current_fps = self.settings.saved_settings["display"]["fps"]
        self.fps_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.04),
            input_type="numbers",
            start_text=str(current_fps),
            reference_resolution=res
        )
        self.main_grid.add_object(fps_label, 4, 0, align="left")
        self.main_grid.add_object(self.fps_input, 4, 1, align="left")
        camera_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Camera Device:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        camera_options = ["Pi Camera", "iDS", "Daheng"]
        current_camera = self.settings.saved_settings["camera"]["device"]
        current_camera_idx = camera_options.index(current_camera) if current_camera in camera_options else 0
        self.camera_dropdown = DropdownMenu(
            rel_pos=(0, 0),
            rel_size=(0.2, 0.04),
            options=camera_options,
            selected_index=current_camera_idx,
            reference_resolution=res
        )
        self.main_grid.add_object(camera_label, 5, 0, align="left")
        self.main_grid.add_object(self.camera_dropdown, 5, 1, align="left")
        cam_res_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Camera Resolution:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        current_cam_res = self.settings.saved_settings["camera"]["resolution"]
        cam_x_label = Label(text="W:", text_color=(200, 200, 200), reference_resolution=res)
        self.cam_res_x_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.04),
            input_type="numbers",
            start_text=str(current_cam_res[0]),
            reference_resolution=res
        )
        cam_y_label = Label(text="H:", text_color=(200, 200, 200), reference_resolution=res)
        self.cam_res_y_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.04),
            input_type="numbers",
            start_text=str(current_cam_res[1]),
            reference_resolution=res
        )
        cam_res_grid = Grid(
            rel_pos=(0, 0),
            rel_size=(0.4, 0.05),
            rows=1,
            cols=4,
            cell_padding=0.05,
            reference_resolution=res
        )
        cam_res_grid.add_object(cam_x_label, 0, 0, align="right")
        cam_res_grid.add_object(self.cam_res_x_input, 0, 1, align="center")
        cam_res_grid.add_object(cam_y_label, 0, 2, align="right")
        cam_res_grid.add_object(self.cam_res_y_input, 0, 3, align="center")
        self.main_grid.add_object(cam_res_label, 6, 0, align="left")
        self.main_grid.add_object(cam_res_grid, 6, 1, align="left")
        exposure_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Exposure:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        current_exposure = self.settings.saved_settings["camera"]["exposure"]
        self.exposure_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.04),
            input_type="all",
            start_text=str(current_exposure),
            reference_resolution=res
        )
        self.main_grid.add_object(exposure_label, 7, 0, align="left")
        self.main_grid.add_object(self.exposure_input, 7, 1, align="left")
        gain_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Gain:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        current_gain = self.settings.saved_settings["camera"]["gain"]
        self.gain_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.04),
            input_type="numbers",
            start_text=str(current_gain),
            reference_resolution=res
        )
        self.main_grid.add_object(gain_label, 8, 0, align="left")
        self.main_grid.add_object(self.gain_input, 8, 1, align="left")
        motor_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Steps per mm (X, Y, Z):",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        motors = self.settings.saved_settings["motors"]
        x_motor_label = Label(text="X:", text_color=(200, 200, 200), reference_resolution=res)
        self.motor_x_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.08, 0.04),
            input_type="numbers",
            start_text=str(motors["x_steps_per_mm"]),
            reference_resolution=res
        )
        y_motor_label = Label(text="Y:", text_color=(200, 200, 200), reference_resolution=res)
        self.motor_y_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.08, 0.04),
            input_type="numbers",
            start_text=str(motors["y_steps_per_mm"]),
            reference_resolution=res
        )
        z_motor_label = Label(text="Z:", text_color=(200, 200, 200), reference_resolution=res)
        self.motor_z_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.08, 0.04),
            input_type="numbers",
            start_text=str(motors["z_steps_per_mm"]),
            reference_resolution=res
        )
        motor_grid = Grid(
            rel_pos=(0, 0),
            rel_size=(0.5, 0.05),
            rows=1,
            cols=6,
            cell_padding=0.05,
            reference_resolution=res
        )
        motor_grid.add_object(x_motor_label, 0, 0, align="right")
        motor_grid.add_object(self.motor_x_input, 0, 1, align="center")
        motor_grid.add_object(y_motor_label, 0, 2, align="right")
        motor_grid.add_object(self.motor_y_input, 0, 3, align="center")
        motor_grid.add_object(z_motor_label, 0, 4, align="right")
        motor_grid.add_object(self.motor_z_input, 0, 5, align="center")
        self.main_grid.add_object(motor_label, 9, 0, align="left")
        self.main_grid.add_object(motor_grid, 9, 1, align="left")
        output_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Output Mode:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        output_options = ["Data Only", "Images Only", "Both"]
        current_output = self.settings.saved_settings["processing"]["output_mode"]
        current_output_idx = output_options.index(current_output) if current_output in output_options else 0
        self.output_dropdown = DropdownMenu(
            rel_pos=(0, 0),
            rel_size=(0.2, 0.04),
            options=output_options,
            selected_index=current_output_idx,
            reference_resolution=res
        )
        self.main_grid.add_object(output_label, 10, 0, align="left")
        self.main_grid.add_object(self.output_dropdown, 10, 1, align="left")
        save_path_label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text="Save Path:",
            text_color=(255, 255, 255),
            reference_resolution=res
        )
        current_path = self.settings.saved_settings["processing"]["save_path"]
        self.save_path_input = InputField(
            rel_pos=(0, 0),
            rel_size=(0.3, 0.04),
            input_type="all",
            start_text=current_path,
            reference_resolution=res
        )
        self.main_grid.add_object(save_path_label, 11, 0, align="left")
        self.main_grid.add_object(self.save_path_input, 11, 1, align="left")
        return
    
    def update_layout(self, width:int, height:int):
        """Update layout when window is resized"""
        self.current_window_size = (width, height)
        self.menu_bar.update_layout((width, height))
        self.main_grid.update_layout((width, height))
        return
    
    def handle_events(self, events:list)->None:
        """Handle pygame events"""
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout(event.w, event.h)
        self.menu_bar.handle_events(events)
        self.main_grid.handle_events(events)
        return
    
    def update(self)->None:
        """Update scene state"""
        self.main_grid.update()
        return
    
    def draw(self, screen)->None:
        """Draw the settings scene"""
        background_color = (30, 30, 30)
        screen.fill(background_color)
        self.menu_bar.draw(screen)
        self.main_grid.draw(screen)
        return
    
    def save_settings(self)->None:
        """Save the current settings"""
        changes_made = {
            "display": False,
            "camera": False,
            "motors": False,
            "processing": False
        }
        display_flag = self.display_radio.get_selected()
        resolution_x = int(self.resolution_x_input.get_text()) if self.resolution_x_input.get_text() else 1366
        resolution_y = int(self.resolution_y_input.get_text()) if self.resolution_y_input.get_text() else 768
        fps = int(self.fps_input.get_text()) if self.fps_input.get_text() else 30
        current_display = self.settings.saved_settings["display"]
        if (display_flag != current_display["display_flag"] or
            [resolution_x, resolution_y] != current_display["resolution"] or
            fps != current_display["fps"]):
            self.settings.save_settings("display", 
                                resolution=[resolution_x, resolution_y],
                                display_flag=display_flag,
                                fps=fps)
            changes_made["display"] = True
        camera_device = self.camera_dropdown.get_selected()
        cam_res_x = int(self.cam_res_x_input.get_text()) if self.cam_res_x_input.get_text() else 1920
        cam_res_y = int(self.cam_res_y_input.get_text()) if self.cam_res_y_input.get_text() else 1080
        exposure = self.exposure_input.get_text()
        gain = float(self.gain_input.get_text()) if self.gain_input.get_text() else 1.0
        current_camera = self.settings.saved_settings["camera"]
        if (camera_device != current_camera["device"] or
            [cam_res_x, cam_res_y] != current_camera["resolution"] or
            exposure != str(current_camera["exposure"]) or
            gain != current_camera["gain"]):
            self.settings.save_settings("camera",
                                   device=camera_device,
                                   resolution=[cam_res_x, cam_res_y],
                                   exposure=exposure,
                                   gain=gain)
            changes_made["camera"] = True
        x_steps = int(self.motor_x_input.get_text()) if self.motor_x_input.get_text() else 200
        y_steps = int(self.motor_y_input.get_text()) if self.motor_y_input.get_text() else 200
        z_steps = int(self.motor_z_input.get_text()) if self.motor_z_input.get_text() else 400
        current_motors = self.settings.saved_settings["motors"]
        if (x_steps != current_motors["x_steps_per_mm"] or
            y_steps != current_motors["y_steps_per_mm"] or
            z_steps != current_motors["z_steps_per_mm"]):
            self.settings.save_settings("motors",
                                    x_steps_per_mm=x_steps,
                                    y_steps_per_mm=y_steps,
                                    z_steps_per_mm=z_steps)
            changes_made["motors"] = True
        output_mode = self.output_dropdown.get_selected()
        save_path = self.save_path_input.get_text()
        current_processing = self.settings.saved_settings["processing"]
        if (output_mode != current_processing["output_mode"] or
            save_path != current_processing["save_path"]):
            self.settings.save_settings("processing",
                                    output_mode=output_mode,
                                    save_path=save_path)
            changes_made["processing"] = True
        for category, changed in changes_made.items():
            if changed and category in self.save_settings_callback:
                self.save_settings_callback[category]()
        return
    
    def cancel_settings(self)->None:
        """Cancel and return to previous scene"""
        self.switch_scene_callback(self.previous_scene)
        return
    
    def on_scene_enter(self)->None:
        """Called when this scene becomes active"""
        display_flag = self.settings.saved_settings["display"]["display_flag"]
        display_options = self.display_radio.options
        if display_flag in display_options:
            self.display_radio.set_selected_index(display_options.index(display_flag))
        resolution = self.settings.saved_settings["display"]["resolution"]
        self.resolution_x_input.set_text(str(resolution[0]))
        self.resolution_y_input.set_text(str(resolution[1]))
        fps = self.settings.saved_settings["display"]["fps"]
        self.fps_input.set_text(str(fps))
        camera_device = self.settings.saved_settings["camera"]["device"]
        camera_options = self.camera_dropdown.options
        if camera_device in camera_options:
            self.camera_dropdown.set_selected_index(camera_options.index(camera_device))
        cam_resolution = self.settings.saved_settings["camera"]["resolution"]
        self.cam_res_x_input.set_text(str(cam_resolution[0]))
        self.cam_res_y_input.set_text(str(cam_resolution[1]))
        exposure = self.settings.saved_settings["camera"]["exposure"]
        self.exposure_input.set_text(str(exposure))
        gain = self.settings.saved_settings["camera"]["gain"]
        self.gain_input.set_text(str(gain))
        motors = self.settings.saved_settings["motors"]
        self.motor_x_input.set_text(str(motors["x_steps_per_mm"]))
        self.motor_y_input.set_text(str(motors["y_steps_per_mm"]))
        self.motor_z_input.set_text(str(motors["z_steps_per_mm"]))
        output_mode = self.settings.saved_settings["processing"]["output_mode"]
        output_options = self.output_dropdown.options
        if output_mode in output_options:
            self.output_dropdown.set_selected_index(output_options.index(output_mode))
        save_path = self.settings.saved_settings["processing"]["save_path"]
        self.save_path_input.set_text(save_path)
        return
    
    def cleanup(self)->None:
        """Cleanup scene resources"""
        pass