from pygame import font, draw, VIDEORESIZE
from UI.base_ui import BaseUI
from typing import Optional, Tuple, Literal

class Label(BaseUI):
    # Constants
    MIN_FONT_SIZE = 8
    FONT_HEIGHT_RATIO = 0.5
    MAX_WIDTH_RATIO = 0.95
    MAX_HEIGHT_RATIO = 0.9
    BACKGROUND_BORDER_RADIUS = 10

    def __init__(self,
                 rel_pos: Tuple[float, float] = (0, 0),
                 rel_size: Tuple[float, float] = (0, 0),
                 s_font: Optional[font.Font] = None,
                 fontsize: int = 32,
                 text: str = "Label",
                 text_color: Tuple[int, int, int] = (255, 255, 255),
                 text_style: Optional[Literal["bold", "italic", "strikethrough", "underline"]] = None,
                 background_color: Optional[Tuple[int, int, int]] = None,
                 reference_resolution: Tuple[int, int] = (1920, 1080)) -> None:
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

    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update label size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        _, _, _, abs_height = self.calculate_absolute_rect(window_size)
        if not self.s_font and self.rect.width > 0 and self.rect.height > 0:
            self.fontsize = self.calculate_optimal_font_size()
            self.font = font.SysFont(None, self.fontsize)
            self._apply_text_style(self.font)
            self.rendered_text = self.font.render(self.text, True, self.text_color)
        return
    
    def update(self) -> None:
        """
        Update the label state (called every frame)
        No per-frame updates needed
        """
        pass
    
    def handle_events(self, events: list) -> None:
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout((event.w, event.h))
        return

    def draw(self, surface, pos: Optional[Tuple[int, int]] = None) -> None:
        """
        Draw the label to the screen
        
        Args:
            surface: Pygame surface to draw on
            pos: Optional position override (x, y)
        """
        if pos:
            self.rect.topleft = pos
        if self.background_color is not None:
            draw.rect(surface, self.background_color, self.rect, border_radius=self.BACKGROUND_BORDER_RADIUS)
            text_rect = self.rendered_text.get_rect(center=self.rect.center)
            surface.blit(self.rendered_text, text_rect.topleft)
        else:
            surface.blit(self.rendered_text, self.rect.topleft)
        return

    def _apply_text_style(self, target_font: font.Font) -> None:
        """
        Apply text style to a font object
        
        Args:
            target_font: pygame font object to apply style to
        """
        target_font.set_bold(False)
        target_font.set_italic(False)
        target_font.set_strikethrough(False)
        target_font.set_underline(False)
        match self.text_style:
            case "bold": target_font.set_bold(True)
            case "italic": target_font.set_italic(True)
            case "striketrhough": target_font.set_strikethrough(True)
            case "underline": target_font.set_underline(True)
        return
    
    def set_text(self, new_text: str) -> None:
        """
        Update the label text and re-render
        
        Args:
            new_text: New text to display
        """
        self.text = new_text
        if not self.s_font and self.rect.width > 0 and self.rect.height > 0:
            self.fontsize = self.calculate_optimal_font_size()
            self.font = font.SysFont(None, self.fontsize)
            self._apply_text_style(self.font)
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        return
    
    def get_text(self) -> str:
        """
        Get the current label text
        
        Returns:
            Current text content
        """
        return self.text
    
    def set_text_color(self, new_color: Tuple[int, int, int]) -> None:
        """
        Update the text color and re-render
        
        Args:
            new_color: New RGB color for text
        """
        self.text_color = new_color
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        return
    
    def set_background_color(self, new_color: Optional[Tuple[int, int, int]]) -> None:
        """
        Update the background color
        
        Args:
            new_color: New RGB color for background (None for transparent)
        """
        self.background_color = new_color
        return
    
    def set_text_style(self, new_style: Optional[Literal["bold", "italic", "strikethrough", "underline"]]) -> None:
        """
        Update the text style and re-render
        
        Args:
            new_style: New style to apply
        """
        self.text_style = new_style
        self._apply_text_style(self.font)
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        return