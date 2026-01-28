from pygame import Rect, draw, surfarray
from numpy import uint8, zeros, rot90, fliplr
from cv2 import cvtColor, COLOR_RGB2BGR, normalize, NORM_MINMAX, line, calcHist
from windows.base_window import BaseWindow
from typing import Tuple, Optional, List
from numpy import ndarray

class HistogramView(BaseWindow):
    # Constants
    HISTOGRAM_BINS = 256
    HISTOGRAM_RANGE = [0, 256]
    UPDATE_INTERVAL = 5

    def __init__(self,
                 rel_pos: Tuple[float, float] = (0.331, 0.661),
                 rel_size: Tuple[float, float] = (0.329, 0.339),
                 reference_resolution: Tuple[int, int] = (1920, 1080),
                 background_color: Tuple[int, int, int] = (0, 0, 0),
                 border_color: Tuple[int, int, int] = (255, 0, 0)):
        """
        Initialize the HistogramView window
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
            background_color: RGB color for background
            border_color: RGB color for border
        """
        super().__init__(rel_pos, rel_size, reference_resolution, background_color, border_color)
        self.histogram_border = Rect(0, 0, 100, 100)
        self.hist = None
        self.hist_surface = None
        self._hist_surface_dirty = True
        self._frame_counter = 0
        return
    
    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update histogram view size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        super().update_layout(window_size)
        border_x = int(self.rel_pos[0] * self.window_width)
        border_y = int(self.rel_pos[1] * self.window_height)
        border_width = int(self.rel_size[0] * self.window_width)
        border_height = int(self.rel_size[1] * self.window_height)
        self.histogram_border = Rect(border_x, border_y, border_width, border_height)
        self.rect = Rect(border_x + 1, border_y + 1, border_width - 2, border_height - 2)
        self._hist_surface_dirty = True
        return
    
    def handle_events(self, events: list) -> None:
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_events(events)
        return
    
    def update(self) -> None:
        """
        Update the histogram view state (called every frame)
        """
        pass
    
    def draw(self, surface) -> None:
        """
        Draw the histogram view to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        if self.rect is None:
            return
        draw.rect(surface, self.border_color, self.histogram_border)
        draw.rect(surface, self.background_color, self.rect)
        if self.hist:
            self._draw_histogram(surface)
        return
    
    def update_from_frame(self, frame: ndarray) -> None:
        """
        Update histogram from a frame (with frame skipping for performance)
        
        Args:
            frame: Image array (numpy array or pygame surface)
        """
        self._frame_counter += 1
        if self._frame_counter >= self.UPDATE_INTERVAL:
            self._frame_counter = 0
            hist = self._calculate_histogram(frame)
            if hist is not None:
                self.set_histogram(hist)
        return
    
    def set_histogram(self, hist: List[ndarray]) -> None:
        """
        Set new histogram data and mark for redraw
        
        Args:
            hist: List of histogram arrays (1 for grayscale, 3 for RGB)
        """
        if hist != self.hist:
            self.hist = hist
            self._hist_surface_dirty = True
        return
    
    def force_update(self, frame: ndarray) -> None:
        """
        Force immediate histogram calculation and update (skips frame counter)
        
        Args:
            frame: Image array (numpy array or pygame surface)
        """
        hist = self._calculate_histogram(frame)
        if hist is not None:
            self.set_histogram(hist)
        return

    def _calculate_histogram(self, frame: ndarray) -> Optional[List[ndarray]]:
        """
        Calculate histogram from image array
        
        Args:
            frame: Image array (numpy array)
                   - Can be RGB color image with shape [height, width, 3]
                   - Can be grayscale image with shape [height, width]
                   - Can be pygame surface (will be converted)
        
        Returns:
            List of histogram arrays, or None on error
        """
        try:
            if hasattr(frame, 'get_size'):
                frame = surfarray.array3d(frame)
            if len(frame.shape) == 2:
                hist = calcHist([frame], [0], None, [self.HISTOGRAM_BINS], self.HISTOGRAM_RANGE)
                return [hist]
            elif len(frame.shape) == 3 and frame.shape[2] == 3:
                hist = [
                    calcHist([frame], [0], None, [self.HISTOGRAM_BINS], self.HISTOGRAM_RANGE),  # Red
                    calcHist([frame], [1], None, [self.HISTOGRAM_BINS], self.HISTOGRAM_RANGE),  # Green
                    calcHist([frame], [2], None, [self.HISTOGRAM_BINS], self.HISTOGRAM_RANGE)   # Blue
                ]
                return hist
            else:
                print(f"Warning: Unexpected frame shape {frame.shape}")
                return None
        except Exception as e:
            print(f"Error calculating histogram: {e}")
            return None

    def _draw_histogram(self, surface) -> None:
        """
        Draw the histogram, using cache if available
        
        Args:
            surface: Pygame surface to draw on
        """
        if self._hist_surface_dirty or self.hist_surface is None:
            self._render_histogram()
            self._hist_surface_dirty = False
        if self.hist_surface:
            surface.blit(self.hist_surface, (self.rect.x, self.rect.y))
        return
    
    def _render_histogram(self) -> None:
        """
        Render histogram to a cached surface (expensive operation)
        """
        try:
            hist_height = self.rect.height
            hist_width = self.rect.width
            normalized_hist = [
                normalize(channel, None, 0, hist_height, NORM_MINMAX) 
                for channel in self.hist
            ]
            hist_img = zeros((hist_height, hist_width, 3), dtype=uint8)
            bin_width = hist_width / self.HISTOGRAM_BINS
            if len(normalized_hist) == 1:
                self._draw_grayscale_histogram(hist_img, normalized_hist[0], bin_width, hist_height)
            elif len(normalized_hist) == 3:
                self._draw_rgb_histogram(hist_img, normalized_hist, bin_width, hist_height)
            hist_img = cvtColor(hist_img, COLOR_RGB2BGR)
            hist_img = rot90(fliplr(hist_img))
            self.hist_surface = surfarray.make_surface(hist_img)
        except Exception as e:
            print(f"Error rendering histogram: {e}")
            self.hist_surface = None
        return
    
    def _draw_grayscale_histogram(self, hist_img: ndarray, hist: ndarray, 
                                   bin_width: float, hist_height: int) -> None:
        """
        Draw grayscale histogram as white lines
        
        Args:
            hist_img: Image to draw on
            hist: Normalized histogram data
            bin_width: Width of each histogram bin in pixels
            hist_height: Height of histogram display
        """
        for i in range(self.HISTOGRAM_BINS - 1):
            x1 = int(i * bin_width)
            x2 = int((i + 1) * bin_width)
            y1 = hist_height - int(hist[i])
            y2 = hist_height - int(hist[i + 1])
            line(hist_img, (x1, y1), (x2, y2), (255, 255, 255), 1)
        return
    
    def _draw_rgb_histogram(self, hist_img: ndarray, hist: List[ndarray], 
                            bin_width: float, hist_height: int) -> None:
        """
        Draw RGB histogram with colored lines (Red, Green, Blue)
        
        Args:
            hist_img: Image to draw on
            hist: List of 3 normalized histogram arrays [R, G, B]
            bin_width: Width of each histogram bin in pixels
            hist_height: Height of histogram display
        """
        colors = [
            (0, 0, 255),
            (0, 255, 0),
            (255, 0, 0)
        ]
        for channel_idx in range(3):
            for i in range(self.HISTOGRAM_BINS - 1):
                x1 = int(i * bin_width)
                x2 = int((i + 1) * bin_width)
                y1 = hist_height - int(hist[channel_idx][i])
                y2 = hist_height - int(hist[channel_idx][i + 1])
                line(hist_img, (x1, y1), (x2, y2), colors[channel_idx], 1)
        return
    
    def clear_histogram(self) -> None:
        """Clear the current histogram display"""
        self.hist = None
        self.hist_surface = None
        self._hist_surface_dirty = True
        return