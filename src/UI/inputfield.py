from pygame import draw, font, MOUSEBUTTONDOWN, KEYDOWN, key, K_BACKSPACE, K_RETURN
from UI.base_ui import BaseUI

class InputField(BaseUI):
    def __init__(self,
                 rel_pos = (0,0),
                 rel_size = None,
                 s_font = None,
                 fontsize = 32,
                 input_type ="all",
                 color_active=(200,200,200),
                 color_inactive=(100,100,100),
                 start_text = None,
                 text_color=(0,0,0),
                 linked_element=None,
                 reference_resolution=(1920,1080)):
        """
        Initialize the InputField
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            s_font: Custom pygame font (if None, uses system font)
            fontsize: Base font size
            input_type: Type of input ("all", "numbers", "letters", "key")
            color_active: RGB color when active/focused
            color_inactive: RGB color when inactive
            start_text: Initial text content
            text_color: RGB color for the text
            linked_element: UI element to sync values with (e.g., Slider)
            reference_resolution: Reference resolution for scaling
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.input_type = input_type
        self.color_active = color_active
        self.color_inactive = color_inactive
        self.text_color = text_color
        self.s_font = s_font
        self.base_fontsize = fontsize
        self.fontsize = fontsize
        self.linked_element = linked_element
        self.font = s_font or font.SysFont(None,fontsize)
        self.text = start_text or ""
        self.rendered_text = self.font.render(self.text,True,self.text_color)
        self.padding = 8
        self.active = False
        self.select_all_on_next_draw = False
        self.wait_key_input = False
        return

    def update_layout(self, window_size):
        """
        Update input field size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        _, _, _, abs_height = self.calculate_absolute_rect(window_size)
        if not self.s_font:
            target_fontsize = int(abs_height * 0.4)
            self.fontsize = max(8, min(target_fontsize, int(abs_height * 0.6)))
            self.font = font.SysFont(None, self.fontsize)
            self.padding = max(5, int(abs_height * 0.15))
        return

    def handle_events(self, events):
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_event(events)
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                was_active = self.active
                self.active = self.rect.collidepoint(event.pos)
                if self.active and not was_active:
                    self.await_key_input = self.input_type == "key"
                    self.select_all_on_next_draw = True
                    return
            if self.active and (event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN):
                if self.select_all_on_next_draw:
                    self.text = ""
                    self.select_all_on_next_draw = False
                if self.input_type == "key" and getattr(self, "await_key_input", False):
                    if event.type == MOUSEBUTTONDOWN:
                        mouse_names = {1: "MOUSE_LEFT", 2: "MOUSE_MIDDLE", 3: "MOUSE_RIGHT"}
                        self.text = mouse_names.get(event.button, f"MOUSE_{event.button}")
                    elif event.type == KEYDOWN:
                        self.text = key.name(event.key)
                    self._update_linked_from_text()
                    self.active = False
                    self.await_key_input = False
                    return
                if event.type == KEYDOWN:
                    if event.key == K_BACKSPACE:
                        self.text = self.text[:-1]
                    elif event.key == K_RETURN:
                        self._update_linked_from_text()
                    else:
                        char = event.unicode
                        if self.input_type == "numbers" and (char.isdigit() or char == "."):
                            self.text += char
                        elif self.input_type == "letters" and char.isalpha():
                            self.text += char
                        elif self.input_type == "all" and char.isalnum():
                            self.text += char
        return

    def _update_linked_from_text(self):
        """
        Update linked element's value from current text
        """
        if self.linked_element:
            try:
                value = float(self.text) if self.input_type == "numbers" else self.text
                self.linked_element.set_value(value)
            except ValueError:
                pass
        return
    
    def sync_from_linked(self):
        """
        Synchronize text from linked element's value
        """
        if self.linked_element:
            val = self.linked_element.get_value()
            if isinstance(val, float):
                if abs(val) < 1:
                    self.text = f"{val:.2f}"
                elif abs(val) < 100:
                    self.text = f"{val:.1f}"
                else:
                    self.text = f"{int(val)}"
            elif isinstance(val, int):
                self.text = str(val)
            else:
                self.text = str(val)
        return

    def link_to(self,other):
        """
        Link this input field to another UI element
        
        Args:
            other: UI element to link to (must have get_value/set_value methods)
        """
        self.linked_element = other
        return
    
    def update(self):
        """
        Update the input field state (called every frame)
        Syncs from linked element when not active
        """
        if not self.active:
            self.sync_from_linked()
        else:
            self._update_linked_from_text()
        return

    def draw(self,surface):
        """
        Draw the input field to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        if self.active:
            color = self.color_active
        else:
            color = self.color_inactive
        draw.rect(surface,color,self.rect, border_radius=5)
        txt_surf = self.font.render(self.text, True,self.text_color)
        max_width = self.rect.width - (2 * self.padding)
        if txt_surf.get_width() > max_width:
            visible_text = self.text
            while len(visible_text) > 0:
                txt_surf = self.font.render("..." + visible_text, True, self.text_color)
                if txt_surf.get_width() <= max_width:
                    break
                visible_text = visible_text[1:]
        surface.blit(txt_surf, (self.rect.x + self.padding, self.rect.y + (self.rect.height-txt_surf.get_height())/2))
        return