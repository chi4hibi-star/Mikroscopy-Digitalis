from pygame import display, FULLSCREEN, RESIZABLE
from settings import Settings
from scenes.settings_scene import SettingsScene
from scenes.image_acquisition_scene import ImageAcquisitionScene
from scenes.algorithm_scene import AlgorithmScene
from scenes.processing_scene import ProcessingScene

class Statemachine:
    def __init__(self,stop_game,change_fps):
        self._stop_game = stop_game
        self._change_game_fps = change_fps
        self.settings = Settings()                                                       #Save the saved sattings as a member Variable with a Scene reset methode
        self.scenes = {}                                                                                            #Create a dict for holding the Scenes
        self.current_scene = None
        self.previous_scene_name = "image_acquisition"
        self.settings_callbacks = {
            "display": self._on_display_settings_changed,
            "camera": self._on_camera_settings_changed,
            "motors": self._on_motors_settings_changed,
            "processing": self._on_processing_settings_changed
        }
        self.shared_camera = None
        return
    
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
                        self.switch_scene
                    )
                    if new_scene.camera_thread:
                        self.shared_camera = new_scene.camera_thread
                case "algorithms":
                    new_scene = AlgorithmScene(
                        self.display_surface,
                        self.settings,
                        self.switch_scene
                    )
                case "processing":
                    new_scene = ProcessingScene(
                        self.display_surface,
                        self.settings,
                        self.switch_scene
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