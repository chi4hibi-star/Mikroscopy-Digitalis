from pygame import display, FULLSCREEN, RESIZABLE
from settings import Settings
from os import makedirs, path
from datetime import datetime
from src.scenes.settings_scene import SettingsScene
from src.scenes.image_acquisition_scene import ImageAcquisitionScene
from src.scenes.algorithm_scene import AlgorithmScene
from src.scenes.processing_scene import ProcessingScene

class Statemachine:
    def __init__(self,stop_game,change_fps):
        self._stop_game = stop_game
        self._change_game_fps = change_fps
        self.settings = Settings()
        self.scenes = {}
        self.current_scene = None
        self.previous_scene_name = "image_acquisition"
        self.settings_callbacks = {
            "display": self._on_display_settings_changed,
            "camera": self._on_camera_settings_changed,
            "motors": self._on_motors_settings_changed,
            "processing": self._on_processing_settings_changed
        }
        self.directories = (None, None, None)  # ADD THIS LINE
        self.directories = self.create_directories()
        self.shared_camera = None
        return

    def create_directories(self):
        """Create or reuse directories"""
        # Initialize with existing directories or None
        working_directory = self.directories[0]
        pipeline_directory = self.directories[1]
        output_directory = self.directories[2]
        
        if not (working_directory and path.exists(working_directory)):
            base_dir = "temp_working_dirs"
            makedirs(base_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            working_directory = path.join(base_dir, f"working_dir_{timestamp}")
            makedirs(working_directory, exist_ok=True)
            print(f"Created new working directory: {working_directory}")
            
        if not (pipeline_directory and path.exists(pipeline_directory)):
            base_dir = "pipeline_dirs"
            makedirs(base_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pipeline_directory = path.join(base_dir, f"pipeline_dir_{timestamp}")
            makedirs(pipeline_directory, exist_ok=True)
            print(f"Created new pipeline directory: {pipeline_directory}")
            
        if not (output_directory and path.exists(output_directory)):
            base_dir = "output_dirs"
            makedirs(base_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_directory = path.join(base_dir, f"output_dir_{timestamp}")
            makedirs(output_directory, exist_ok=True)
            print(f"Created new output directory: {output_directory}")
            
        return working_directory, pipeline_directory, output_directory
    
    #reset all scenes
    def _on_display_settings_changed(self):
        game_fps = self.settings.saved_settings["display"]["fps"]
        del self.display_surface
        self.scenes.clear()
        self.new_display()
        self._change_game_fps(game_fps)
        self.switch_scene("settings")
        return
    
    #Not implemented yet
    def _on_camera_settings_changed(self):
        pass

    #Not implemented yet
    def _on_motors_settings_changed(self):
        pass
    
    #Not implemented yet
    def _on_processing_settings_changed(self):
        pass

    def new_display(self):
        if self.settings.saved_settings["display"]["display_flag"] == "RESIZABLE":
            self.display_surface = display.set_mode(
                self.settings.saved_settings["display"]["resolution"], RESIZABLE)
        elif self.settings.saved_settings["display"]["display_flag"] == "FULLSCREEN":
            self.display_surface = display.set_mode((0, 0), FULLSCREEN)
        elif self.settings.saved_settings["display"]["display_flag"] == "FIXED":
            self.display_surface = display.set_mode(
                self.settings.saved_settings["display"]["resolution"])
        return
    
    def switch_scene(self,new_scene_name):
        if new_scene_name == "quit":
            self._stop_game()
            return
        if self.current_scene and new_scene_name == "settings":
            for name, scene in self.scenes.items():
                if scene == self.current_scene:
                    self.previous_scene_name = name
                    break
        elif new_scene_name not in self.scenes:                                                                         #if the new_scene doesn't exist yet, create one
            match new_scene_name:
                case "image_acquisition":
                    new_scene = ImageAcquisitionScene(
                        self.display_surface,
                        self.settings,
                        self.switch_scene,
                        self.directories
                    )
                    if new_scene.camera_thread:
                        self.shared_camera = new_scene.camera_thread
                case "algorithms":
                    new_scene = AlgorithmScene(
                        self.display_surface,
                        self.settings,
                        self.switch_scene,
                        self.directories
                    )
                case "processing":
                    new_scene = ProcessingScene(
                        self.display_surface,
                        self.settings,
                        self.switch_scene,
                        self.directories
                    )
                    new_scene.camera_thread = self.shared_camera
                case "settings":
                    new_scene = SettingsScene(
                        self.display_surface,
                        self.settings,
                        self.switch_scene,
                        self.settings_callbacks,
                        self.previous_scene_name
                    )
            self.scenes[new_scene_name] = new_scene                                                                   #Add the new_scene to the dict
        self.set_current_scene(new_scene_name)                                                                         #Switch to the new Scene as the current active one
        return
    
    def set_current_scene(self,new_scene_name):
        if new_scene_name in self.scenes:
            self.current_scene = self.scenes[new_scene_name]
            self.current_scene.on_scene_enter()                                                                 #If the Scene has a on_scene_enter methode, call it
        return
    
    def cleanup(self):
        for scene in self.scenes.values():
            scene.cleanup()                                                                                           #Call the cleanup methode of every existing Scene
        return