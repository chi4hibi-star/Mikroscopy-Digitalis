from abc import ABC,abstractmethod
from pygame import Rect,VIDEORESIZE,font
from typing import Tuple, Optional

class BaseUI(ABC):
    @abstractmethod
    def __init__(self,rel_pos=(0, 0),rel_size=(0, 0),reference_resolution=(1920, 1080)):
        """
        Base initialization for all UI elements
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
        """
        self.rel_pos = rel_pos
        self.rel_size = rel_size
        self.reference_resolution = reference_resolution
        self.current_window_size = None
        self._grid_align = None
        self._grid_rel_pos = None
        self._grid_managed = False
        self.rect = Rect(0, 0, 10, 10)
        return

    @abstractmethod
    def update_layout(self):
        pass

    @abstractmethod
    def handle_events(self):
        pass
    
    @abstractmethod
    def update(self):
        pass
    
    @abstractmethod
    def draw(self):
        pass

    def calculate_absolute_rect(self, window_size: Tuple[int, int]) -> Tuple[int, int, int, int]:
        """
        Calculate absolute position and size from relative values
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
            
        Returns:
            Tuple of (abs_x, abs_y, abs_width, abs_height)
        """
        window_width, window_height = window_size
        abs_x = int(self.rel_pos[0] * window_width)
        abs_y = int(self.rel_pos[1] * window_height)
        abs_width = int(self.rel_size[0] * window_width)
        abs_height = int(self.rel_size[1] * window_height)
        if not self._grid_managed:
            self.rect = Rect(abs_x, abs_y, abs_width, abs_height)
        return abs_x, abs_y, abs_width, abs_height
    
    def get_scale_factor(self, window_size: Tuple[int, int]) -> float:
        """
        Calculate scale factor based on window height
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
            
        Returns:
            Scale factor as float
        """
        window_height = window_size[1]
        return window_height / self.reference_resolution[1]
    
    def should_update_layout(self, window_size: Tuple[int, int]) -> bool:
        """
        Check if layout needs to be updated
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
            
        Returns:
            True if layout should be updated, False otherwise
        """
        if self.current_window_size != window_size:
            self.current_window_size = window_size
            return True
        return False
    
    def handle_resize_event(self, events: list) -> bool:
        """
        Common event handling for VIDEORESIZE events
        
        Args:
            events: List of pygame events
            
        Returns:
            True if resize event was handled, False otherwise
        """
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout((event.w, event.h))
                return True
        return False
    
    def calculate_optimal_font_size(self, 
                                    text: str, 
                                    max_width: int, 
                                    max_height: int,
                                    base_fontsize: int,
                                    min_fontsize: int = 8,
                                    max_scale: float = 2.0,
                                    s_font: Optional[font.Font] = None,
                                    text_color: Tuple[int, int, int] = (255, 255, 255),
                                    apply_style_func: Optional[callable] = None) -> int:
        """
        Calculate optimal font size using binary search
        
        Args:
            text: Text to fit
            max_width: Maximum width available
            max_height: Maximum height available
            base_fontsize: Base font size to scale from
            min_fontsize: Minimum font size
            max_scale: Maximum scale factor
            s_font: Custom font (if provided, returns base_fontsize)
            text_color: Color for test rendering
            apply_style_func: Optional function to apply text style to font
            
        Returns:
            Optimal font size
        """
        if s_font:
            return base_fontsize
        min_size = min_fontsize
        max_size = int(base_fontsize * max_scale)
        best_size = min_size
        while min_size <= max_size:
            mid_size = (min_size + max_size) // 2
            test_font = font.SysFont(None, mid_size)
            if apply_style_func:
                apply_style_func(test_font)
            test_render = test_font.render(text, True, text_color)
            if test_render.get_width() <= max_width and test_render.get_height() <= max_height:
                best_size = mid_size
                min_size = mid_size + 1
            else:
                max_size = mid_size - 1
        return best_size
    
    def scale_border_radius(self, base_radius: int, window_size: Tuple[int, int]) -> int:
        """
        Scale border radius based on window size
        
        Args:
            base_radius: Base border radius at reference resolution
            window_size: Current window size
            
        Returns:
            Scaled border radius
        """
        scale_factor = self.get_scale_factor(window_size)
        return max(0, int(base_radius * scale_factor))