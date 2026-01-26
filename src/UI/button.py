from pygame import font, mouse, draw, MOUSEBUTTONUP, MOUSEBUTTONDOWN
from UI.base_ui import BaseUI
from typing import Callable, Tuple, Optional

class Button(BaseUI):
    # Constants
    MIN_FONT_SIZE = 8
    MAX_FONT_SCALE = 2.0

    def __init__(
            self,
            text:str='Button',
            rel_pos:Optional[Tuple[float,float]]=None,
            rel_size:Optional[Tuple[float,float]]=None,
            s_font:Optional[font.Font]=None,
            fontsize:int=32,
            callback:Callable=lambda: None,
            base_color:Tuple[int,int,int]=(70, 70, 200),
            hover_color:Tuple[int,int,int]=(100, 100, 240),
            text_color:Tuple[int,int,int]=(180, 180, 180),
            pressed_text_color:Tuple[int,int,int]=(255, 255, 255),
            disabled_color:Tuple[int,int,int]=(50, 50, 50),
            disabled_text_color:Tuple[int,int,int]=(100, 100, 100),
            border_radius:int=10,
            text_padding:int=10,
            text_align: str = "center",
            enabled:bool=True,
            reference_resolution:Tuple[int,int]=(1920, 1080)) -> None:
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
            text_align: Text alignment ("center", "left", "right")
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
        self.text_align = text_align
        self.enabled = enabled
        self.is_pressed = False
        #Initialize font and randered text 
        self.font = s_font or font.SysFont(None, fontsize)
        self.rendered_text = None
        self._last_text_color = None
        self._rander_text(self.text_color)
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
        self.border_radius = max(0, int(self.base_border_radius * scale_factor))
        if not self.s_font and self.rect.width > 0 and self.rect.height > 0:
            max_w = self.rect.width - 2 * self.text_padding
            max_h = self.rect.height - 2 * self.text_padding
            self.fontsize = self._calculate_optimal_font_size(self.text,max_w,max_h)
            self.font = font.SysFont(None,self.fontsize)
            self._render_text(self.text_color)
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

    def update(self) -> None:
        """
        Update the button state (called every frame)
        No per-frame updates needed
        """
        pass

    def draw(self, surface, pos:Optional[Tuple[int,int]]=None)->None:
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
        if self._last_text_color != text_color:
            self._render_text(text_color)
        if self.text_align == "left":
            text_rect = self.rendered_text.get_rect(
                midleft=(self.rect.left+self.text_padding,self.rect.centery)
            )
        elif self.text_align == "right":
            text_rect = self.rendered_text.get_rect(
                midleft=(self.rect.right-self.text_padding,self.rect.centery)
            )
        else: #center
            text_rect = self.rendered_text.get_rect(center=self.rect.center)
        surface.blit(self.rendered_text, text_rect.topleft)
        return
    
    def _calculate_optimal_font_size(self,text:str, max_width:int, max_height:int)->int:
        '''
        Calculate optimal font size using binary search
        
        args:
            text: Text to fit
            max_width: Maximum width available
            max_height: Maximum height available

        Returns:
            Optimal font size
        '''
        min_size = self.MIN_FONT_SIZE
        max_size = int(self.base_fontsize * self.MAX_FONT_SCALE)
        best_size = min_size
        while min_size <= max_size:
            mid_size = (min_size + max_size) // 2
            test_font = font.SysFont(None,mid_size)
            test_render = test_font.render(text,True,self.text_color)
            if test_render.get_width() <= max_width and test_render.get_height() <= max_height:
                best_size = mid_size
                mid_size += 1
            else:
                max_size = mid_size - 1
        return best_size
    
    def _render_text(self, color:Tuple[int,int,int])->None:
        '''
        Render text with current font and cache it
        
        Args:
            color: RGB color for text
        '''
        self.rendered_text = self.font.render(self.text,True,color)
        self._last_text_color = color
        return

    def set_enabled(self, enabled:bool)->None:
        """
        Enable or disable the button
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        if not enabled:
            self.is_pressed = False
        return

    def set_text(self, new_text:str)->None:
        """
        Update the button text
        
        Args:
            new_text: New text to display
        """
        self.text = new_text
        self.rendered_text = self.font.render(self.text, True, self.text_color)
        if not self.s_font and self.rect.width > 0 and self.rect.height > 0:
            max_w = self.rect.width - 2 * self.text_padding
            max_h = self.rect.height - 2 * self.text_padding
            self.fontsize = self._calculate_optimal_font_size(self.text, max_w, max_h)
            self.font = font.SysFont(None, self.fontsize)
        self._render_text(self._last_text_color or self.text_color)
        return