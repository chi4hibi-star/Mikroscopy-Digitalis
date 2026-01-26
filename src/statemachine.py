import pygame
from settings import Settings
from scenes.settings_scene import SettingsScene
from scenes.image_acquisition_scene import ImageAcquisitionScene
from scenes.algorithm_scene import AlgorithmScene
from scenes.processing_scene import ProcessingScene

class Statemachine:
    def __init__(self,stop_game,change_fps):
        self._stop_game = stop_game
        self._change_game_fps = change_fps
        self.settings = Settings(self.save_settings_callback)                                                       #Save the saved sattings as a member Variable with a Scene reset methode
        self.scenes = {}                                                                                            #Create a dict for holding the Scenes
        self.current_scene = None
        return
    
    #Deletes all the Scenes and the display and creates a new one
    def save_settings_callback(self,game_fps):
        del self.display_surface
        self.scenes.clear()
        self.new_display()
        self._change_game_fps(game_fps)
        self.switch_scene("settings")
        return
    
    #Create new Display and set mode
    def new_display(self):
        if self.settings.saved_settings["display"]["display_flag"] == "RESIZABLE":
            self.display_surface = pygame.display.set_mode(
                self.settings.saved_settings["display"]["resolution"],pygame.RESIZABLE)
        elif self.settings.saved_settings["display"]["display_flag"] == "FULLSCREEN":
            self.display_surface = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
        return
    
    def switch_scene(self,new_scene_name):
        if new_scene_name == "quit":
            self._stop_game()
            return
        elif new_scene_name not in self.scenes:                                                                         #if the new_scene doesn't exist yet, create one
            match new_scene_name:
                case "image_acquisition":
                    new_scene = ImageAcquisitionScene(self.display_surface,self.settings,self.switch_scene)
                case "algorithms":
                    new_scene = AlgorithmScene(self.display_surface,self.settings,self.switch_scene)
                case "processing":
                    new_scene = ProcessingScene(self.display_surface,self.settings,self.switch_scene)
                case "settings":
                    new_scene = SettingsScene(self.display_surface,self.settings,self.switch_scene,self.save_settings_callback)
            self.scenes[new_scene_name] = new_scene                                                                    #Add the new_scene to the dict
        self.set_current_scene(new_scene_name)                                                                         #Switch to the new Scene as the current active one
        return
    
    def set_current_scene(self,new_scene_name):
        if new_scene_name in self.scenes:
            self.current_scene = self.scenes[new_scene_name]
            if hasattr(self.current_scene, 'on_scene_enter'):
                self.current_scene.on_scene_enter()                                                                 #If the Scene has a on_scene_enter methode, call it
        return
    
    def cleanup(self):
        for scene in self.scenes.values():
            scene.cleanup()                                                                                           #Call the cleanup methode of every existing Scene
        return