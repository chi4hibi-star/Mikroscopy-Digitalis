from pygame import draw, VIDEORESIZE
from cv2 import cvtColor, COLOR_RGB2GRAY
from numpy import mean
from UI.base_ui import BaseUI

class Indicator(BaseUI):
    def __init__(self,
                 rel_pos=(0,0),
                 rel_size=(0,0),
                 status="red",
                 reference_resolution=(1920, 1080),
                 background_color=(50,50,50),
                 border_color=(100,100,100),
                 border_radius=5):
        """
        Initialize the Indicator
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size for the topleft point
            rel_size: Relative size (width, height) as fraction of window size
            status: Initial status ("red", "yellow", or "green")
            reference_resolution: Reference resolution for scaling (width, height)
            background_color: RGB color for the background
            border_color: RGB color for the border
            border_width: Width of the border in pixels
            border_radius: Radius for rounded corners on background rectangle
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.status = status
        self.background_color = background_color
        self.border_color = border_color
        self.base_border_radius = border_radius
        self.border_radius = border_radius
        self.colors = {
            "red": (220, 50, 50),
            "yellow": (240, 200, 50),
            "green": (50, 220, 80)
        }
        self.radius = 25
        return
    
    def update_layout(self,window_size):
        if not self.should_update_layout(window_size):
            return
        _, _, abs_width, abs_height = self.calculate_absolute_rect(window_size)
        self.radius = int(min(abs_width,abs_height) * 0.4)
        scale_factor = self.get_scale_factor(window_size)
        self.border_radius = max(0,int(self.base_border_radius*scale_factor))
        return
    
    def handle_events(self, events):
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
    
    def set_status(self, frame):
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
            if len(frame.shape)==2:
                gray = frame
            elif len(frame.shape)==3 and frame.shape[2]==3:
                gray = cvtColor(frame,COLOR_RGB2GRAY)
            else:
                print(f"Warning:Unexptected frame shape {frame.shape}")
                self.status = "red"
                return
            brightness = mean(gray)
            if 100 <= brightness <= 156:
                self.status = "green"
            elif (frame == 255).any():
                self.status = "yellow"
            else:
                self.status = "red"
        except Exception as e:
            print(f"Error analyzing frame in Indicator: {e}")
            self.status = "red"
        return
