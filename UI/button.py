from pygame import font, mouse, draw, MOUSEBUTTONUP, MOUSEBUTTONDOWN
from UI.base_ui import BaseUI

class Button(BaseUI):
    def __init__(
            self,
            text='Button',
            rel_pos=None,
            rel_size=None,
            s_font=None,
            fontsize=32,
            callback=lambda: None,
            base_color=(70, 70, 200),
            hover_color=(100, 100, 240),
            text_color=(180, 180, 180),
            pressed_text_color=(255, 255, 255),
            disabled_color=(50, 50, 50),
            disabled_text_color=(100, 100, 100),
            border_radius=10,
            text_padding=10,
            enabled=True,
            reference_resolution=(1920, 1080)):
        """
        Initialize the Button
        
        Args:
            text: Button text to display
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            s_font: Custom pygame font (if None, uses system font)
            fontsize: Base font size
            callback: Function to call when button is clicked
            base_color: RGB color for normal state
            hover_color: RGB color when mouse hovers over button
            text_color: RGB color for text (normal and hover)
            pressed_text_color: RGB color for text when pressed
            disabled_color: RGB color when button is disabled
            disabled_text_color: RGB color for text when disabled
            border_radius: Radius for rounded corners
            text_padding: Padding around text inside button
            enabled: Whether button is initially enabled
            reference_resolution: Reference resolution for scaling
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.text = text
        self.s_font = s_font
        self.base_fontsize = fontsize
        self.fontsize = fontsize
        self.callback = callback
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.pressed_text_color = pressed_text_color
        self.disabled_color = disabled_color
        self.disabled_text_color = disabled_text_color
        self.base_border_radius = border_radius
        self.border_radius = border_radius
        self.text_padding = text_padding
        self.enabled = enabled
        self.is_pressed = False
        self.font = s_font or font.SysFont(None, fontsize)
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        return
    
    def update_layout(self, window_size):
        """
        Update button size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        self.calculate_absolute_rect(window_size)
        scale_factor = self.get_scale_factor(window_size)
        if not self.s_font:
            new_size = max(12, int(self.base_fontsize * scale_factor))
            f = font.SysFont(None, new_size)
            test = f.render(self.text, True, self.text_color)
            max_w = self.rect.width - 2 * self.text_padding
            max_h = self.rect.height - 2 * self.text_padding
            while new_size > 12 and (test.get_width() > max_w or test.get_height() > max_h):
                new_size -= 1
                f = font.SysFont(None, new_size)
                test = f.render(self.text, True, self.text_color)
            while new_size < self.base_fontsize * 2:  # Allow up to 2x base size
                test_size = new_size + 2
                f_test = font.SysFont(None, test_size)
                test_render = f_test.render(self.text, True, self.text_color)
                if test_render.get_width() <= max_w and test_render.get_height() <= max_h:
                    new_size = test_size
                    f = f_test
                    test = test_render
                else:
                    break
            self.font = f
            self.fontsize = new_size
            self.rendered_text = test
        self.border_radius = max(0, int(self.base_border_radius * scale_factor))
        return
    
    def handle_events(self, events):
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_event(events)
        if not self.enabled:
            return
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                self.is_pressed = self.rect.collidepoint(event.pos)
            elif event.type == MOUSEBUTTONUP:
                if self.is_pressed and self.rect.collidepoint(event.pos):
                    self.callback()
                self.is_pressed = False
        return

    def update(self):
        """
        Update the button state (called every frame)
        No per-frame updates needed
        """
        pass

    def draw(self, surface, pos=None):
        """
        Draw the button to the screen
        
        Args:
            surface: Pygame surface to draw on
            pos: Optional position override (x, y)
        """
        if pos:
            self.rect.topleft = pos
        if not self.enabled:
            color = self.disabled_color
            text_color = self.disabled_text_color
        else:
            hover = self.rect.collidepoint(mouse.get_pos())
            color = self.hover_color if hover else self.base_color
            text_color = self.pressed_text_color if (hover and self.is_pressed) else self.text_color
        draw.rect(surface, color, self.rect, border_radius=self.border_radius)
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect.topleft)
        return

    def set_enabled(self, enabled):
        """
        Enable or disable the button
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        if not enabled:
            self.is_pressed = False
        return

    def set_text(self, new_text):
        """
        Update the button text
        
        Args:
            new_text: New text to display
        """
        self.text = new_text
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        if self.rect.width > 0 and self.rect.height > 0 and not self.s_font:
            test = self.font.render(self.text, True, self.text_color)
            max_w = self.rect.width - 2 * self.text_padding
            max_h = self.rect.height - 2 * self.text_padding
            new_size = self.fontsize
            while new_size > 8 and (test.get_width() > max_w or test.get_height() > max_h):
                new_size -= 1
                f = font.SysFont(None, new_size)
                test = f.render(self.text, True, self.text_color)
            if new_size != self.fontsize:
                self.font = f
                self.fontsize = new_size
                self.rendered_text = test
        return