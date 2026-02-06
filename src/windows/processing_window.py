from pygame import Rect, draw, font, transform, Surface
from windows.base_window import BaseWindow
from windows.node_canvas import NodeCanvas
from typing import Optional

class ProcessingViewport(BaseWindow):
    """
    Multi-mode viewport for pipeline/input/output/live visualization
    
    View Modes:
    - pipeline: Show pipeline node graph
    - input: Show selected input image
    - output: Show processed output image
    - live: Show live processed camera feed
    """
    
    # Colors
    BORDER_COLOR = (100, 100, 100)
    TEXT_COLOR = (255, 255, 255)
    PLACEHOLDER_COLOR = (150, 150, 150)
    LABEL_BG_COLOR = (40, 40, 40)
    
    def __init__(self, 
                 rel_pos=(0.251, 0.051), 
                 rel_size=(0.498, 0.648), 
                 reference_resolution=(1920, 1080), 
                 background_color=(30, 30, 30)):
        """
        Initialize the Processing Viewport
        
        Args:
            rel_pos: Relative position (x, y)
            rel_size: Relative size (width, height)
            reference_resolution: Reference resolution for scaling
            background_color: RGB background color
        """
        super().__init__(rel_pos, rel_size, reference_resolution, background_color)
        self.current_mode = "input"
        self.pipeline_canvas: Optional[NodeCanvas] = None
        self.input_image: Optional[Surface] = None
        self.output_image: Optional[Surface] = None
        self.live_frame: Optional[Surface] = None
        self.font = font.SysFont(None, 24)
        self.small_font = font.SysFont(None, 18)
        return
    
    def set_view_mode(self, mode: str):
        """
        Set the current view mode
        
        Args:
            mode: View mode ('pipeline', 'input', 'output', 'live')
        """
        if mode in ["pipeline", "input", "output", "live"]:
            self.current_mode = mode
        else:
            print(f"Invalid view mode: {mode}")
        return
    
    def set_pipeline_canvas(self, canvas: Optional[NodeCanvas]):
        """
        Set the pipeline canvas for pipeline view
        
        Args:
            canvas: NodeCanvas instance or None
        """
        self.pipeline_canvas = canvas
        return
    
    def set_input_image(self, image: Optional[Surface]):
        """
        Set input image for preview
        
        Args:
            image: Pygame surface of input image
        """
        self.input_image = image
        return
    
    def set_output_image(self, image: Optional[Surface]):
        """
        Set output image for display
        
        Args:
            image: Pygame surface of processed output
        """
        self.output_image = image
        return
    
    def set_live_frame(self, frame: Optional[Surface]):
        """
        Set current live frame
        
        Args:
            frame: Pygame surface of live processed frame
        """
        self.live_frame = frame
        return
    
    def update_layout(self, window_size):
        """
        Update viewport size and position
        
        Args:
            window_size: Tuple of (width, height)
        """
        super().update_layout(window_size)
        if self.pipeline_canvas:
            self.pipeline_canvas.update_layout(window_size)
        return
    
    def handle_events(self, events: list):
        """
        Handle events for viewport
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_events(events)
        if self.current_mode == "pipeline" and self.pipeline_canvas:
            self.pipeline_canvas.handle_events(events)
        return
    
    def update(self):
        """Update viewport state (called every frame)"""
        if self.current_mode == "pipeline" and self.pipeline_canvas:
            self.pipeline_canvas.update()
        return
    
    def draw(self, surface: Surface):
        """
        Draw viewport based on current mode
        
        Args:
            surface: Pygame surface to draw on
        """
        draw.rect(surface, self.background_color, self.rect)
        draw.rect(surface, self.BORDER_COLOR, self.rect, 2)
        clip_rect = surface.get_clip()
        surface.set_clip(self.rect)
        content_rect = self._get_content_rect()
        if self.current_mode == "pipeline":
            self._draw_pipeline_view(surface, content_rect)
        elif self.current_mode == "input":
            self._draw_input_view(surface, content_rect)
        elif self.current_mode == "output":
            self._draw_output_view(surface, content_rect)
        elif self.current_mode == "live":
            self._draw_live_view(surface, content_rect)
        surface.set_clip(clip_rect)
        return
    
    def _get_content_rect(self) -> Rect:
        """
        Get the content area rect (viewport minus padding for labels)
        
        Returns:
            Rect for content area
        """
        padding_top = 30
        padding_sides = 10
        return Rect(
            self.rect.x + padding_sides,
            self.rect.y + padding_top,
            self.rect.width - 2 * padding_sides,
            self.rect.height - padding_top - padding_sides
        )
    
    def _draw_pipeline_view(self, surface: Surface, content_rect: Rect):
        """
        Draw pipeline node canvas
        
        Args:
            surface: Pygame surface to draw on
            content_rect: Rectangle for content area
        """
        self._draw_mode_label(surface, "Pipeline View")
        if self.pipeline_canvas:
            old_rect = self.pipeline_canvas.rect
            self.pipeline_canvas.rect = content_rect
            self.pipeline_canvas.draw(surface)
            self.pipeline_canvas.rect = old_rect
        else:
            self._draw_placeholder(surface, content_rect, "No Pipeline Selected")
        return
    
    def _draw_input_view(self, surface: Surface, content_rect: Rect):
        """
        Draw input image preview
        
        Args:
            surface: Pygame surface to draw on
            content_rect: Rectangle for content area
        """
        self._draw_mode_label(surface, "Input Image")
        if self.input_image:
            self._draw_scaled_image(surface, self.input_image, content_rect)
        else:
            self._draw_placeholder(surface, content_rect, "No Input Image Selected")
        return
    
    def _draw_output_view(self, surface: Surface, content_rect: Rect):
        """
        Draw output image
        
        Args:
            surface: Pygame surface to draw on
            content_rect: Rectangle for content area
        """
        self._draw_mode_label(surface, "Processed Output")
        
        if self.output_image:
            self._draw_scaled_image(surface, self.output_image, content_rect)
        else:
            self._draw_placeholder(surface, content_rect, "No Output Yet - Process an Image")
        return

    def _draw_live_view(self, surface: Surface, content_rect: Rect):
        """
        Draw live processed camera feed
        
        Args:
            surface: Pygame surface to draw on
            content_rect: Rectangle for content area
        """
        self._draw_mode_label(surface, "Live Processing")
        if self.live_frame:
            self._draw_scaled_image(surface, self.live_frame, content_rect)
        else:
            self._draw_placeholder(surface, content_rect, "Live View Not Active")
        return
    
    def _draw_scaled_image(self, surface: Surface, image: Surface, rect: Rect):
        """
        Draw an image scaled to fit within rect (maintaining aspect ratio)
        
        Args:
            surface: Pygame surface to draw on
            image: Image to display
            rect: Rectangle to fit image within
        """
        if image is None:
            return
        img_width, img_height = image.get_size()
        scale_x = rect.width / img_width
        scale_y = rect.height / img_height
        scale = min(scale_x, scale_y, 1.0)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        if scale < 1.0 or (new_width != img_width or new_height != img_height):
            try:
                scaled_img = transform.smoothscale(image, (new_width, new_height))
            except Exception as e:
                print(f"Error scaling image: {e}")
                scaled_img = image
        else:
            scaled_img = image
        x_offset = (rect.width - scaled_img.get_width()) // 2
        y_offset = (rect.height - scaled_img.get_height()) // 2
        surface.blit(scaled_img, (rect.x + x_offset, rect.y + y_offset))
        info_text = f"{img_width} × {img_height}"
        info_surface = self.small_font.render(info_text, True, self.TEXT_COLOR)
        info_bg_rect = Rect(
            rect.x + rect.width - info_surface.get_width() - 10,
            rect.y + rect.height - info_surface.get_height() - 5,
            info_surface.get_width() + 6,
            info_surface.get_height() + 4
        )
        draw.rect(surface, self.LABEL_BG_COLOR, info_bg_rect)
        surface.blit(info_surface, (info_bg_rect.x + 3, info_bg_rect.y + 2))
        return
    
    def _draw_placeholder(self, surface: Surface, rect: Rect, text: str):
        """
        Draw placeholder text when no content available
        
        Args:
            surface: Pygame surface to draw on
            rect: Rectangle for content area
            text: Placeholder text to display
        """
        text_surface = self.font.render(text, True, self.PLACEHOLDER_COLOR)
        text_rect = text_surface.get_rect(center=rect.center)
        surface.blit(text_surface, text_rect)
        return
    
    def _draw_mode_label(self, surface: Surface, label: str):
        """
        Draw mode label at top of viewport
        
        Args:
            surface: Pygame surface to draw on
            label: Label text to display
        """
        label_surface = self.font.render(label, True, self.TEXT_COLOR)
        label_x = self.rect.x + 10
        label_y = self.rect.y + 5
        bg_rect = Rect(
            label_x - 3,
            label_y - 2,
            label_surface.get_width() + 6,
            label_surface.get_height() + 4
        )
        draw.rect(surface, self.LABEL_BG_COLOR, bg_rect)
        surface.blit(label_surface, (label_x, label_y))
        return