from pygame import draw, VIDEORESIZE
from cv2 import cvtColor, COLOR_RGB2GRAY
from numpy import mean, ndarray
from UI.base_ui import BaseUI
from typing import Tuple, Optional, Literal

class Indicator(BaseUI):
    # Constants
    DEFAULT_RADIUS = 25
    RADIUS_RATIO = 0.4
    BRIGHTNESS_MIN = 100
    BRIGHTNESS_MAX = 156
    SATURATED_VALUE = 255

    def __init__(self,
                 rel_pos: Tuple[float, float] = (0, 0),
                 rel_size: Tuple[float, float] = (0, 0),
                 status: Literal["red", "yellow", "green"] = "red",
                 reference_resolution: Tuple[int, int] = (1920, 1080),
                 background_color: Tuple[int, int, int] = (50, 50, 50),
                 border_radius: int = 5) -> None:
        """
        Initialize the Indicator
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size for the topleft point
            rel_size: Relative size (width, height) as fraction of window size
            status: Initial status ("red", "yellow", or "green")
            reference_resolution: Reference resolution for scaling (width, height)
            background_color: RGB color for the background
            border_width: Width of the border in pixels
            border_radius: Radius for rounded corners on background rectangle
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.status = status
        self.background_color = background_color
        self.base_border_radius = border_radius
        self.border_radius = border_radius
        self.colors = {
            "red": (220, 50, 50),
            "yellow": (240, 200, 50),
            "green": (50, 220, 80)
        }
        self.radius = self.DEFAULT_RADIUS
        return
    
    def update_layout(self,window_size: Tuple[int, int]) -> None:
        """
        Update indicator size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        _, _, abs_width, abs_height = self.calculate_absolute_rect(window_size)
        self.radius = int(min(abs_width,abs_height) * self.RADIUS_RATIO)
        scale_factor = self.get_scale_factor(window_size)
        self.border_radius = max(0,int(self.base_border_radius*scale_factor))
        return
    
    def handle_events(self, events: list) -> None:
        """
        Handle pygame events (indicator doesn't need event handling currently)
        
        Args:
            events: List of pygame events
        """
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout((event.w, event.h))
        return
    
    def update(self):
        """
        Update the indicator state (called every frame)
        No per-frame updates needed
        """
        pass
    
    def draw(self, surface):
        """
        Draw the indicator to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        draw.rect(surface, self.background_color, self.rect, border_radius=self.border_radius)
        color = self.colors.get(self.status, self.colors["red"])
        center_x = self.rect.centerx
        center_y = self.rect.centery
        draw.circle(surface, color, (center_x, center_y), self.radius)
        return
    
    def set_status(self, frame: ndarray) -> None:
        """
        Analyze frame and update status based on brightness
        
        Args:
            frame: Image array (numpy array)
                   - Can be RGB color image with shape [height, width, 3]
                   - Can be grayscale image with shape [height, width]
        
        Status determination:
            - green: brightness in range [100, 156]
            - yellow: any pixel is saturated (value == 255)
            - red: otherwise (too dark or other issues)
        """
        try:
            gray = self._convert_to_grayscale(frame)
            if gray is None:
                self.status = "red"
                return
            brightness = mean(gray)
            if (frame == self.SATURATED_VALUE).any():
                self.status = "yellow"
            elif self.BRIGHTNESS_MIN <= brightness <= self.BRIGHTNESS_MAX:
                self.status = "green"
            else:
                self.status = "red"
        except Exception as e:
            print(f"Error analyzing frame in Indicator: {e}")
            self.status = "red"
        return

    def _convert_to_grayscale(self, frame: ndarray) -> Optional[ndarray]:
        """
        Convert frame to grayscale if needed
        
        Args:
            frame: Input image array
        
        Returns:
            Grayscale image, or None if invalid format
        """
        if len(frame.shape) == 2:
            return frame
        elif len(frame.shape) == 3 and frame.shape[2] == 3:
            return cvtColor(frame, COLOR_RGB2GRAY)
        else:
            print(f"Warning: Unexpected frame shape {frame.shape}")
            return None
    
    def set_status_manual(self, status: Literal["red", "yellow", "green"]) -> None:
        """
        Manually set the indicator status without frame analysis
        
        Args:
            status: Status to set ("red", "yellow", or "green")
        """
        if status in self.colors:
            self.status = status
        else:
            print(f"Warning: Invalid status '{status}'. Must be 'red', 'yellow', or 'green'.")
        return
    
    def get_status(self) -> str:
        """
        Get the current status
        
        Returns:
            Current status string ("red", "yellow", or "green")
        """
        return self.status