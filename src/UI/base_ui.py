from abc import ABC,abstractmethod
from pygame import Rect,VIDEORESIZE

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
        if not self._grid_managed:
            self.rect = Rect(abs_x, abs_y, abs_width, abs_height)
        return abs_x, abs_y, abs_width, abs_height
    
    def get_scale_factor(self, window_size):
        """
        Calculate scale factor based on window height
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
            
        Returns:
            Scale factor as float
        """
        window_height = window_size[1]
        return window_height / self.reference_resolution[1]
    
    def should_update_layout(self, window_size):
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
    
    def handle_resize_event(self, events):
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