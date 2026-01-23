from pygame import display, RESIZABLE, FULLSCREEN
from settings import Settings
from settings_scene import SettingsScene
from image_acquisition_scene import ImageAcquisitionScene
from algorithm_scene import AlgorithmScene
from processing_scene import ProcessingScene

class Statemachine:
    def __init__(self,change_running):
        self.settings = Settings(self.save_settings_callback)                                                       #Save the saved sattings as a member Variable with a Scene reset methode
        self.scenes = {}                                                                                            #Create a dict for holding the Scenes
        self.current_scene = None
        self.change_running = change_running
        return
    
    def set_current_scene(self,call):
        if call in self.scenes:
            self.current_scene = self.scenes[call]
            if hasattr(self.current_scene, 'on_scene_enter'):
                self.current_scene.on_scene_enter()                                                                 #If the Scene has a on_scene_enter methode, call it
        return

    #Create new Display and set mode
    def new_display(self):
        if self.settings.saved_settings["display_flag"] == "RESIZABLE":
            self.display_surface = display.set_mode(self.settings.saved_settings["resolution"],RESIZABLE)
        elif self.settings.saved_settings["display_flag"] == "FULLSCREEN":
            self.display_surface = display.set_mode((0,0),FULLSCREEN)
        return
    
    #Deletes all the Scenes and the display and creates a new one
    def save_settings_callback(self):
        del self.display_surface
        self.scenes.clear()
        self.new_display()
        self.switch_scene("settings")
        return
    
    def switch_scene(self,new_scene_name):
        if new_scene_name == "quit":
            self.change_running()
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
    
    def cleanup(self):
        for scene in self.scenes.values():
            scene.cleanup()                                                                                           #Call the cleanup methode of every existing Scene
        return