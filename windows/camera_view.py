from pygame import Rect,font,draw,transform,mouse,MOUSEWHEEL,MOUSEBUTTONDOWN,MOUSEBUTTONUP,MOUSEMOTION
from windows.base_window import BaseWindow

class CameraView(BaseWindow):
    def __init__(self,
                 rel_pos=(0.001, 0.051),
                 rel_size=(0.659, 0.609),
                 reference_resolution=(1920, 1080),
                 background_color=(0, 0, 0),
                 border_color=(255, 0, 0)):
        """
        Initialize the CameraView window
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
            background_color: RGB color for background
            border_color: RGB color for border
        """
        super().__init__(rel_pos, rel_size, reference_resolution, background_color, border_color)
        self.border_rect = Rect(0, 0, 100, 100)
        self.viewing_mode = "live"
        self.base_font_size = 48
        self.live_frame = None
        self.selected_image = None
        self.rotation_angle = 0
        self.zoom_level = 100
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.is_dragging = False
        self.last_mouse_pos = None
        self.mouse_coords = None
        self.coord_font = None
        self.base_coord_font_size = 16
        return
    
    def update_layout(self, window_size):
        """
        Update camera view size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        super().update_layout(window_size)
        border_x = int(self.rel_pos[0] * self.window_width)
        border_y = int(self.rel_pos[1] * self.window_height)
        border_width = int(self.rel_size[0] * self.window_width)
        border_height = int(self.rel_size[1] * self.window_height)
        self.border_rect = Rect(border_x, border_y, border_width, border_height)
        content_x = border_x + 1
        content_y = border_y + 1
        content_width = border_width - 2
        content_height = border_height - 2
        self.rect = Rect(content_x, content_y, content_width, content_height)
        scale_factor = self.get_scale_factor()
        self.coord_font_size = max(12, int(self.base_coord_font_size * scale_factor))
        self.coord_font = font.SysFont(None, self.coord_font_size)
        return
    
    def handle_events(self, events):
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_events(events)
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.rect.collidepoint(event.pos):
                        if self.zoom_level > 100:
                            self.is_dragging = True
                            self.last_mouse_pos = event.pos
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.is_dragging = False
                    self.last_mouse_pos = None
            elif event.type == MOUSEMOTION:
                if self.is_dragging and self.last_mouse_pos:
                    delta_x = event.pos[0] - self.last_mouse_pos[0]
                    delta_y = event.pos[1] - self.last_mouse_pos[1]
                    self.pan_offset_x -= delta_x
                    self.pan_offset_y -= delta_y
                    self.last_mouse_pos = event.pos
            elif event.type == MOUSEWHEEL:
                if self.rect.collidepoint(mouse.get_pos()):
                    if event.y > 0:
                        self.zoom_level = min(300,self.zoom_level + 10)
                    else:
                        self.zoom_level = max(50,self.zoom_level -10)
                    if self.zoom_level <= 100:
                        self.pan_offset_x = 0
                        self.pan_offset_y = 0
                        self.zoom_level = 100
        return
    
    def update(self):
        """
        Update the camera view state (called every frame)
        """
        mouse_pos = mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            display_frame = None
            if self.viewing_mode == "live":
                display_frame = self.live_frame
            elif self.viewing_mode == "image":
                display_frame = self.selected_image
            if display_frame:
                self.mouse_coords = self._get_image_coordinates(mouse_pos, display_frame)
            else:
                self.mouse_coords = None
        else:
            self.mouse_coords = None
        return
    
    def draw(self, surface):
        """
        Draw the camera view to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        draw.rect(surface, self.border_color, self.border_rect)
        draw.rect(surface, self.background_color, self.rect)
        display_frame = None
        if self.viewing_mode == "live":
            display_frame = self.live_frame
        elif self.viewing_mode == "image":
            display_frame = self.selected_image
        if display_frame:
            self._draw_frame(surface, display_frame)
        else:
            self._draw_no_content_message(surface)
        if self.mouse_coords and self.coord_font:
            coord_text = f"X: {self.mouse_coords[0]}, Y: {self.mouse_coords[1]}"
            text_surface = self.coord_font.render(coord_text, True, (255, 255, 255))
            text_bg = text_surface.get_rect()
            text_bg.bottomright = (self.rect.right - 5, self.rect.bottom - 5)
            bg_rect = text_bg.inflate(10, 6)
            draw.rect(surface, (0, 0, 0, 180), bg_rect)
            draw.rect(surface, (100, 100, 100), bg_rect, 1)
            surface.blit(text_surface, text_bg)
        return
    
    def _get_image_coordinates(self, mouse_pos, frame):
        """Convert screen mouse position to image coordinates"""
        rotated_frame = frame
        if self.rotation_angle == 90:
            rotated_frame = transform.rotate(frame, -90)
        elif self.rotation_angle == 180:
            rotated_frame = transform.rotate(frame, 180)
        elif self.rotation_angle == 270:
            rotated_frame = transform.rotate(frame, 90)
        frame_width, frame_height = rotated_frame.get_size()
        view_width, view_height = self.rect.size
        scale_x = view_width / frame_width
        scale_y = view_height / frame_height
        base_scale = min(scale_x, scale_y)
        zoom_factor = self.zoom_level / 100.0
        scale = base_scale * zoom_factor
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        if self.zoom_level <= 100:
            x_offset = (view_width - new_width) // 2
            y_offset = (view_height - new_height) // 2
        else:
            max_pan_x = max(0, (new_width - view_width) // 2)
            max_pan_y = max(0, (new_height - view_height) // 2)
            clamped_pan_x = max(-max_pan_x, min(max_pan_x, self.pan_offset_x))
            clamped_pan_y = max(-max_pan_y, min(max_pan_y, self.pan_offset_y))
            x_offset = (view_width - new_width) // 2 - clamped_pan_x
            y_offset = (view_height - new_height) // 2 - clamped_pan_y
        relative_x = mouse_pos[0] - self.rect.x - x_offset
        relative_y = mouse_pos[1] - self.rect.y - y_offset
        if 0 <= relative_x < new_width and 0 <= relative_y < new_height:
            img_x = int(relative_x / scale)
            img_y = int(relative_y / scale)
            if 0 <= img_x < frame_width and 0 <= img_y < frame_height:
                return (img_x, img_y)
        return None
    
    def _draw_frame(self, surface, frame):
        """
        Draw a frame (live or selected image) with transformations
        
        Args:
            surface: Pygame surface to draw on
            frame: Pygame surface containing the frame to display
        """
        rotated_frame = frame
        if self.rotation_angle == 90:
            rotated_frame = transform.rotate(frame, -90)
        elif self.rotation_angle == 180:
            rotated_frame = transform.rotate(frame, 180)
        elif self.rotation_angle == 270:
            rotated_frame = transform.rotate(frame, 90)
        frame_width, frame_height = rotated_frame.get_size()
        view_width, view_height = self.rect.size
        scale_x = view_width / frame_width
        scale_y = view_height / frame_height
        base_scale = min(scale_x, scale_y)
        zoom_factor = self.zoom_level / 100.0
        scale = base_scale * zoom_factor
        new_width = int(frame_width * scale)
        new_height = int(frame_height * scale)
        scaled_frame = transform.smoothscale(rotated_frame, (new_width, new_height))
        if self.zoom_level <= 100:
            x_offset = (view_width - new_width) // 2
            y_offset = (view_height - new_height) // 2
            surface.blit(scaled_frame, (self.rect.x + x_offset, self.rect.y + y_offset))
        else:
            max_pan_x = max(0, (new_width - view_width) // 2)
            max_pan_y = max(0, (new_height - view_height) // 2)
            self.pan_offset_x = max(-max_pan_x, min(max_pan_x, self.pan_offset_x))
            self.pan_offset_y = max(-max_pan_y, min(max_pan_y, self.pan_offset_y))
            x_offset = (view_width - new_width) // 2 - self.pan_offset_x
            y_offset = (view_height - new_height) // 2 - self.pan_offset_y
            clip_rect = surface.get_clip()
            surface.set_clip(self.rect)
            surface.blit(scaled_frame, (self.rect.x + x_offset, self.rect.y + y_offset))
            surface.set_clip(clip_rect)
        return
    
    def _draw_no_content_message(self, surface):
        """
        Draw a message when no content is available
        
        Args:
            surface: Pygame surface to draw on
        """
        if self.viewing_mode == "live":
            text = self.font.render("No Camera Feed", True, (150, 150, 150))
        else:
            text = self.font.render("No Image Selected", True, (150, 150, 150))
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)
        return
    
    def set_live_frame(self, frame):
        """
        Set the current live camera frame
        
        Args:
            frame: Pygame surface containing the camera frame
        """
        self.live_frame = frame
        return
    
    def set_selected_image(self, image):
        """
        Set the selected image to display
        
        Args:
            image: Pygame surface containing the selected image
        """
        self.selected_image = image
        self.viewing_mode = "image"
        self.zoom_level = 100
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        return
    
    def switch_to_live(self):
        """Switch to live camera view mode"""
        self.viewing_mode = "live"
        self.selected_image = None
        return
    
    def rotate_view(self):
        """Rotate the view by 90 degrees clockwise"""
        self.rotation_angle = (self.rotation_angle + 90) % 360
        return
    
    def set_zoom(self, zoom_level):
        """
        Set the zoom level
        
        Args:
            zoom_level: Zoom percentage (100 = original size)
        """
        if zoom_level > 0:
            self.zoom_level = zoom_level
        if zoom_level <= 100:
            self.pan_offset_x = 0
            self.pan_offset_y = 0
        return
    
    def zoom_home(self):
        """Reset zoom to 100% and center the view"""
        self.zoom_level = 100
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        return
    
    def get_rotation_angle(self):
        """Get the current rotation angle"""
        return self.rotation_angle
    
    def get_zoom_level(self):
        """Get the current zoom level"""
        return self.zoom_level