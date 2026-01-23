from json import dump, load

class Settings():
    def __init__(self,save_settings_callback):
        self.save_settings_callback = save_settings_callback
        self.saved_settings = self.load_settings()
        return

    def save_settings(self,new_settings):
        existing_settings = self.saved_settings.copy()
        existing_settings.update({
            "resolution": new_settings[0],
            "display_flag": new_settings[1],
            "language": new_settings[2],
            "camera": new_settings[3]
        })
        with open("settings.json", "w") as f:
            dump(existing_settings, f, indent=4)
        self.saved_settings = self.load_settings()
        return

    def load_settings(self):
        with open("settings.json","r") as f:
            a = load(f)
        return a