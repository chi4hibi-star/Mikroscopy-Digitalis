from json import dump, load

class Settings():
    def __init__(self,save_settings_callback):
        self.save_settings_callback = save_settings_callback
        self.saved_settings = self.load_settings()
        return

    def save_settings(self, category, **kwargs):
        '''
        Save settings for a specific category.
        
        Example: save_settings("display", resolution=[1920, 1080], fps=60)
        '''
        if category not in self.saved_settings:
            self.saved_settings[category] = {}
        self.saved_settings[category].update(kwargs)
        with open("settings.json", "w") as f:
            dump(self.saved_settings, f, indent=4)
        self.saved_settings = self.load_settings()
        if category == "display" and "fps" in kwargs:
            self.save_settings_callback(kwargs["fps"])
        return

    def load_settings(self):
        try:
            with open("settings.json","r") as f:
                a = load(f)
            return a
        except FileNotFoundError:
            defaults = {
                "display": {
                    "resolution": [1366, 768],
                    "display_flag": "RESIZABLE",
                    "fps": 30
                },
                "camera": {
                    "device": "iDS",
                    "resolution": [1920, 1080],
                    "exposure": "auto"
                },
                "motors": {
                    "x_steps_per_mm": 200,
                    "y_steps_per_mm": 200,
                    "z_steps_per_mm": 400
                },
                "processing": {
                    "output_mode": "Data Only"
                },
                "interface": {
                    "language": "German"
                }
            }
            with open("settings.json", "w") as f:
                dump(defaults, f, indent=4)
            return defaults