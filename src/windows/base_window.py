from abc import ABC,abstractmethod
from pygame import Rect,font,VIDEORESIZE

class BaseWindow(ABC):
    @abstractmethod
    def __init__(self,
                 rel_pos=(0, 0),
                 rel_size=(0, 0),
                 reference_resolution=(1920, 1080),
                 background_color=None,
                 border_color=None):
        """
        Initialize base window
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
            background_color: RGB color for background (None for no background)
            border_color: RGB color for border (None for no border)
        """
        self.rel_pos = rel_pos
        self.rel_size = rel_size
        self.reference_resolution = reference_resolution
        self.current_window_size = None
        self.background_color = background_color
        self.border_color = border_color
        self.rect = Rect(0, 0, 100, 100)
        self.base_font_size = 20
        self.font_size = 20
        self.font = None
        return

    @abstractmethod
    def update_layout(self,window_size):
        """
        Update window size and position based on window size.
        Can be extended by subclasses but should call super().update_layout()
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if self.current_window_size == window_size:
            return
        self.current_window_size = window_size
        self.window_width, self.window_height = window_size
        abs_x = int(self.rel_pos[0] * self.window_width)
        abs_y = int(self.rel_pos[1] * self.window_height)
        abs_width = int(self.rel_size[0] * self.window_width)
        abs_height = int(self.rel_size[1] * self.window_height)
        self.rect = Rect(abs_x, abs_y, abs_width, abs_height)
        if self.font is None and hasattr(self, 'base_font_size'):
            scale_factor = self.window_height / self.reference_resolution[1]
            self.font_size = max(12, int(self.base_font_size * scale_factor))
            self.font = font.SysFont(None, self.font_size)
        return

    @abstractmethod
    def handle_events(self):
        pass
    
    @abstractmethod
    def update(self):
        pass
    
    @abstractmethod
    def draw(self):
        pass

    def handle_resize_events(self, events):
        """
        Handle VIDEORESIZE events - common pattern across all windows
        
        Args:
            events: List of pygame events
            
        Returns:
            True if resize was handled, False otherwise
        """
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout((event.w, event.h))
                return True
        return False
    
    def get_scale_factor(self, window_size=None):
        """
        Get the current scale factor based on window height
        
        Args:
            window_size: Optional window size tuple, uses current_window_size if None
            
        Returns:
            Scale factor as float
        """
        if window_size is None:
            window_size = self.current_window_size
        if window_size is None:
            return 1.0
        return window_size[1] / self.reference_resolution[1]
    
    def calculate_absolute_rect(self, window_size):
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
        return abs_x, abs_y, abs_width, abs_height

    def create_scaled_font(self, base_size, window_size=None, custom_font=None):
        """
        Create a font scaled to the current window size
        
        Args:
            base_size: Base font size at reference resolution
            window_size: Optional window size tuple, uses current_window_size if None
            custom_font: Optional custom font (if None, uses system font)
            
        Returns:
            Scaled pygame font object
        """
        if custom_font is not None:
            return custom_font
        if window_size is None:
            window_size = self.current_window_size
        scale_factor = self.get_scale_factor(window_size)
        scaled_size = max(8, int(base_size * scale_factor))
        return font.SysFont(None, scaled_size)
    
    