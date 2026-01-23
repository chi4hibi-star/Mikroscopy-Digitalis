from pygame import Rect, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, draw
from UI.base_ui import BaseUI

class Slider(BaseUI):
    def __init__(self,
                 rel_pos=(0, 0),
                 rel_size=(0.1, 0.03),
                 min_val=0,
                 max_val=1,
                 start_val=None,
                 color=(0, 200, 0),
                 background_color=(100, 100, 100),
                 handle_color=(255, 255, 255),
                 reference_resolution=(1920, 1080)):
        """
        Initialize the Slider
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            min_val: Minimum value
            max_val: Maximum value
            start_val: Initial value (if None, uses midpoint)
            color: RGB color for filled portion
            background_color: RGB color for unfilled portion
            handle_color: RGB color for draggable handle
            reference_resolution: Reference resolution for scaling
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.min_val = min_val
        self.max_val = max_val
        self.color = color
        self.background_color = background_color
        self.handle_color = handle_color
        if start_val is None:
            self.value = (min_val + max_val) / 2
        else:
            self.value = max(min_val, min(max_val, start_val))
        self.base_handle_width = 10
        self.handle_width = 10
        self.dragging = False
        return
    
    def update_layout(self, window_size):
        """
        Update slider size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        self.calculate_absolute_rect(window_size)
        scale_factor = self.get_scale_factor(window_size)
        self.handle_width = max(8, int(self.base_handle_width * scale_factor))
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
                if self.get_handle_rect().collidepoint(event.pos):
                    self.dragging = True
                elif self.rect.collidepoint(event.pos):
                    self.update_value_from_mouse(event.pos[0])
                    self.dragging = True
            elif event.type == MOUSEBUTTONUP:
                self.dragging = False
            elif event.type == MOUSEMOTION and self.dragging:
                self.update_value_from_mouse(event.pos[0])
        return
    
    def update(self):
        """
        Update the slider state (called every frame)
        No per-frame updates needed
        """
        pass
    
    def draw(self, surface):
        """
        Draw the slider to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        draw.rect(surface, self.background_color, self.rect)
        if self.max_val != self.min_val:
            fill_width = ((self.value - self.min_val) / (self.max_val - self.min_val)) * self.rect.width
        else:
            fill_width = 0
        fill_rect = Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        draw.rect(surface, self.color, fill_rect)
        draw.rect(surface, self.handle_color, self.get_handle_rect())
        return
    
    def get_handle_rect(self):
        """
        Calculate the rectangle for the draggable handle
        
        Returns:
            Rect: The handle rectangle
        """
        if self.max_val == self.min_val:
            percent = 0
        else:
            percent = (self.value - self.min_val) / (self.max_val - self.min_val)
        x = self.rect.x + percent * self.rect.width
        return Rect(x - self.handle_width / 2, self.rect.y, self.handle_width, self.rect.height)
    
    def update_value_from_mouse(self, mouse_x):
        """
        Update slider value based on mouse x position
        
        Args:
            mouse_x: Mouse x coordinate
        """
        relative_x = max(self.rect.x, min(mouse_x, self.rect.x + self.rect.width))
        if self.rect.width > 0:
            percent = (relative_x - self.rect.x) / self.rect.width
            self.value = self.min_val + percent * (self.max_val - self.min_val)
        return
    
    def get_value(self):
        """
        Get the current slider value
        
        Returns:
            The current value
        """
        return self.value
    
    def set_value(self, val):
        """
        Set the slider value
        
        Args:
            val: New value (will be clamped to min/max range)
        """
        self.value = max(self.min_val, min(self.max_val, val))
        return