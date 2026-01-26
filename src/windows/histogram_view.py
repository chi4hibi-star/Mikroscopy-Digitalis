from pygame import Rect, draw, surfarray
from numpy import uint8, zeros, rot90, fliplr
from cv2 import cvtColor, COLOR_BGR2RGB, normalize, NORM_MINMAX, line, calcHist
from windows.base_window import BaseWindow

class HistogramView(BaseWindow):
    def __init__(self,
                 rel_pos=(0.331, 0.661),
                 rel_size=(0.329, 0.339),
                 reference_resolution=(1920, 1080),
                 background_color=(0, 0, 0),
                 border_color=(255, 0, 0)):
        super().__init__(rel_pos, rel_size, reference_resolution, background_color, border_color)
        self.histogram_border = Rect(0, 0, 100, 100)
        self.hist = None
        self.hist_surface = None
        return
    
    def update_layout(self, window_size):
        super().update_layout(window_size)
        border_x = int(self.rel_pos[0] * self.window_width)
        border_y = int(self.rel_pos[1] * self.window_height)
        border_width = int(self.rel_size[0] * self.window_width)
        border_height = int(self.rel_size[1] * self.window_height)
        self.histogram_border = Rect(border_x, border_y, border_width, border_height)
        self.rect = Rect(border_x + 1, border_y + 1, border_width - 2, border_height - 2)
        return
    
    def handle_events(self, events):
        self.handle_resize_events(events)
        return
    
    def update(self):
        pass
    
    def draw(self, screen):
        if self.rect is None:
            return
        draw.rect(screen, self.border_color, self.histogram_border)
        draw.rect(screen, self.background_color, self.rect)
        if self.hist:
            self._draw_histogram(screen)
        return
    
    def _draw_histogram(self, screen):
        hist_height = self.rect.height
        hist_width = self.rect.width
        hist = [normalize(channel, None, 0, hist_height, NORM_MINMAX) for channel in self.hist]
        hist_img = zeros((hist_height, hist_width, 3), dtype=uint8)
        bin_width = self.rect.width / 256
        if len(hist) == 1:
            for i in range(255):
                x1 = int(i * bin_width)
                x2 = int((i + 1) * bin_width)
                y1 = hist_height - int(hist[0][i])
                y2 = hist_height - int(hist[0][i])
                line(hist_img, (x1, y1), (x2, y2), (255, 255, 255), 1)
        elif len(hist) == 3:
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
            for c in range(3):
                for i in range(255):
                    x1 = int(i * bin_width)
                    x2 = int((i + 1) * bin_width)
                    y1 = hist_height - int(hist[c][i])
                    y2 = hist_height - int(hist[c][i + 1])
                    line(hist_img, (x1, y1), (x2, y2), colors[c], 1)
        hist_img = cvtColor(hist_img, COLOR_BGR2RGB)
        self.hist_surface = surfarray.make_surface(rot90(fliplr(hist_img)))
        screen.blit(self.hist_surface, (self.rect.x, self.rect.y))
        return
    
    def calculate_histogram(self, img_array):
        try:
            bgr_frame = cvtColor(img_array, COLOR_BGR2RGB)
            if len(bgr_frame.shape) == 2:
                hist = calcHist([bgr_frame], [0], None, [256], [0, 256])
                return [hist]
            elif len(bgr_frame.shape) == 3:
                hist = [
                    calcHist([bgr_frame], [0], None, [256], [0, 256]),
                    calcHist([bgr_frame], [1], None, [256], [0, 256]),
                    calcHist([bgr_frame], [2], None, [256], [0, 256])
                ]
                return hist
        except Exception as e:
            print(f"Error calculating histogram: {e}")
            return None