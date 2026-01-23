from pygame import font, draw, VIDEORESIZE
from UI.base_ui import BaseUI

class Label(BaseUI):
    def __init__(self,
                 rel_pos=(0,0),
                 rel_size = (0,0),
                 s_font=None,
                 fontsize=32,
                 text="Label",
                 text_color=(255,255,255),
                 text_style = None,
                 background_color = None,
                 reference_resolution=(1920,1080)):
        """
        Initialize the Label
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            s_font: Custom pygame font (if None, uses system font)
            fontsize: Base font size
            text: Text to display
            text_color: RGB color for the text
            text_style: Style ("bold", "italic", "strikethrough", "underline", or None)
            background_color: RGB color for background (None for transparent)
            reference_resolution: Reference resolution for scaling
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.text = text
        self.text_color = text_color
        self.text_style = text_style
        self.background_color = background_color
        self.s_font = s_font
        self.base_fontsize = fontsize
        self.fontsize = fontsize
        self.font = s_font or font.SysFont(None,fontsize)
        self._apply_text_style(self.font)
        self.rendered_text = self.font.render(self.text,True,self.text_color)
        return

    def update_layout(self, window_size):
        """
        Update label size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        _, _, _, abs_height = self.calculate_absolute_rect(window_size)
        if not self.s_font:
            target_fontsize = int(abs_height * 0.5)
            self.font = font.SysFont(None, target_fontsize)
            self._apply_text_style(self.font)
            test_text = self.font.render(self.text, True, self.text_color)
            max_width = self.rect.width * 0.95
            max_height = self.rect.height * 0.9
            while target_fontsize > 8 and (test_text.get_width() > max_width or 
                                          test_text.get_height() > max_height):
                target_fontsize -= 1
                self.font = font.SysFont(None, target_fontsize)
                self._apply_text_style(self.font)
                test_text = self.font.render(self.text, True, self.text_color)
            self.fontsize = target_fontsize
            self.rendered_text = test_text
        return
    
    def update(self):
        """
        Update the label state (called every frame)
        No per-frame updates needed
        """
        pass
    
    def handle_events(self, events):
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout((event.w, event.h))
        return

    def draw(self, surface, pos=None):
        """
        Draw the label to the screen
        
        Args:
            surface: Pygame surface to draw on
            pos: Optional position override (x, y)
        """
        if pos:
            self.rect.topleft = pos
        if self.background_color is not None:
            draw.rect(surface, self.background_color, self.rect, border_radius=10)
            text_rect = self.rendered_text.get_rect()
            surface.blit(self.rendered_text, (
                self.rect.x + (self.rect.width - text_rect.width) / 2,
                self.rect.y + (self.rect.height - text_rect.height) / 2
            ))
        else:
            surface.blit(self.rendered_text, self.rect.topleft)
        return

    def _apply_text_style(self, target_font):
        """
        Apply text style to a font object
        
        Args:
            target_font: pygame font object to apply style to
        """
        if self.text_style == "bold":
            target_font.set_bold(True)
        elif self.text_style == "italic":
            target_font.set_italic(True)
        elif self.text_style == "strikethrough":
            target_font.set_strikethrough(True)
        elif self.text_style == "underline":
            target_font.set_underline(True)
        return
    
    def set_text(self, new_text):
        """
        Update the label text and re-render
        
        Args:
            new_text: New text to display
        """
        self.text = new_text
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        if self.rect.width > 0 and self.rect.height > 0:
            test_text = self.font.render(self.text, True, self.text_color)
            max_width = self.rect.width * 0.95
            max_height = self.rect.height * 0.9
            fontsize = self.fontsize
            while fontsize > 8 and (test_text.get_width() > max_width or 
                                   test_text.get_height() > max_height):
                fontsize -= 1
                temp_font = font.SysFont(None, fontsize)
                self._apply_text_style(temp_font)
                test_text = temp_font.render(self.text, True, self.text_color)
            if fontsize != self.fontsize:
                self.font = temp_font
                self.fontsize = fontsize
                self.rendered_text = test_text
        return