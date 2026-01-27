from pygame import Rect, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, draw
from UI.base_ui import BaseUI
from typing import Tuple, Optional, Callable

class Slider(BaseUI):
    # Constants
    DEFAULT_HANDLE_WIDTH = 10
    MIN_HANDLE_WIDTH = 8
    
    def __init__(self,
                 rel_pos: Tuple[float, float] = (0, 0),
                 rel_size: Tuple[float, float] = (0.1, 0.03),
                 min_val: float = 0,
                 max_val: float = 1,
                 start_val: Optional[float] = None,
                 color: Tuple[int, int, int] = (0, 200, 0),
                 background_color: Tuple[int, int, int] = (100, 100, 100),
                 handle_color: Tuple[int, int, int] = (255, 255, 255),
                 on_change_callback: Optional[Callable[[float], None]] = None,
                 reference_resolution: Tuple[int, int] = (1920, 1080)) -> None:
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
            on_change_callback: Optional callback function called when value changes
            reference_resolution: Reference resolution for scaling
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.min_val = min_val
        self.max_val = max_val
        self.color = color
        self.background_color = background_color
        self.handle_color = handle_color
        self.on_change_callback = on_change_callback
        if start_val is None:
            self.value = (min_val + max_val) / 2
        else:
            self.value = self._clamp_value(start_val)
        self.base_handle_width = self.DEFAULT_HANDLE_WIDTH
        self.handle_width = self.DEFAULT_HANDLE_WIDTH
        self.dragging = False
        return
    
    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update slider size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        self.calculate_absolute_rect(window_size)
        scale_factor = self.get_scale_factor(window_size)
        self.handle_width=max(self.MIN_HANDLE_WIDTH,int(self.base_handle_width*scale_factor))
        return
    
    def handle_events(self, events: list) -> None:
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_event(events)
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)
            elif event.type == MOUSEBUTTONUP:
                self._handle_mouse_up(event)
            elif event.type == MOUSEMOTION and self.dragging:
                self._handle_mouse_motion(event)
        return
    
    def update(self) -> None:
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
        fill_width = self._value_to_percent() * self.rect.width
        fill_rect = Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        draw.rect(surface, self.color, fill_rect)
        draw.rect(surface, self.handle_color, self.get_handle_rect())
        return
    
    def _clamp_value(self, val: float) -> float:
        """
        Clamp value to min/max range
        
        Args:
            val: Value to clamp
        
        Returns:
            Clamped value
        """
        return max(self.min_val, min(self.max_val, val))
    
    def _value_to_percent(self) -> float:
        """
        Convert current value to percentage (0.0 to 1.0)
        
        Returns:
            Percentage as float
        """
        if self.max_val == self.min_val:
            return 0.0
        return (self.value - self.min_val) / (self.max_val - self.min_val)
    
    def _percent_to_value(self, percent: float) -> float:
        """
        Convert percentage to value
        
        Args:
            percent: Percentage (0.0 to 1.0)
        
        Returns:
            Corresponding value
        """
        return self.min_val + percent * (self.max_val - self.min_val)
    
    def _handle_mouse_down(self, event) -> None:
        """
        Handle mouse button down event
        
        Args:
            event: Pygame MOUSEBUTTONDOWN event
        """
        if self.get_handle_rect().collidepoint(event.pos):
            self.dragging = True
        elif self.rect.collidepoint(event.pos):
            self._update_value_from_mouse(event.pos[0])
            self.dragging = True
        return
    
    def _handle_mouse_up(self, event) -> None:
        """
        Handle mouse button up event
        
        Args:
            event: Pygame MOUSEBUTTONUP event
        """
        self.dragging = False
        return
    
    def _handle_mouse_motion(self, event) -> None:
        """
        Handle mouse motion while dragging
        
        Args:
            event: Pygame MOUSEMOTION event
        """
        self._update_value_from_mouse(event.pos[0])
        return
    
    def get_handle_rect(self) -> Rect:
        """
        Calculate the rectangle for the draggable handle
        
        Returns:
            Rect: The handle rectangle
        """
        percent = self._value_to_percent()
        x = self.rect.x + percent * self.rect.width
        return Rect(x - self.handle_width / 2, self.rect.y, self.handle_width, self.rect.height)
    
    def _update_value_from_mouse(self, mouse_x: int) -> None:
        """
        Update slider value based on mouse x position
        
        Args:
            mouse_x: Mouse x coordinate
        """
        relative_x = max(self.rect.x, min(mouse_x, self.rect.x + self.rect.width))
        if self.rect.width > 0:
            percent = (relative_x - self.rect.x) / self.rect.width
            new_value = self._percent_to_value(percent)
            if new_value != self.value:
                self.value = new_value
                if self.on_change_callback:
                    self.on_change_callback(self.value)
        return
    
    def get_value(self) -> float:
        """
        Get the current slider value
        
        Returns:
            The current value
        """
        return self.value
    
    def set_value(self, val: float) -> None:
        """
        Set the slider value
        
        Args:
            val: New value (will be clamped to min/max range)
        """
        new_value = self._clamp_value(val)
        if new_value != self.value:
            self.value = new_value
            if self.on_change_callback:
                self.on_change_callback(self.value)
        return
    
    def set_range(self, min_val: float, max_val: float) -> None:
        """
        Update the min/max range of the slider
        
        Args:
            min_val: New minimum value
            max_val: New maximum value
        """
        self.min_val = min_val
        self.max_val = max_val
        self.value = self._clamp_value(self.value)
        return
    
    def get_range(self) -> Tuple[float, float]:
        """
        Get the current min/max range
        
        Returns:
            Tuple of (min_val, max_val)
        """
        return (self.min_val, self.max_val)
    
    def set_colors(self, 
                   color: Optional[Tuple[int, int, int]] = None,
                   background_color: Optional[Tuple[int, int, int]] = None,
                   handle_color: Optional[Tuple[int, int, int]] = None) -> None:
        """
        Update slider colors
        
        Args:
            color: RGB color for filled portion (None to keep current)
            background_color: RGB color for unfilled portion (None to keep current)
            handle_color: RGB color for handle (None to keep current)
        """
        if color is not None:
            self.color = color
        if background_color is not None:
            self.background_color = background_color
        if handle_color is not None:
            self.handle_color = handle_color
        return