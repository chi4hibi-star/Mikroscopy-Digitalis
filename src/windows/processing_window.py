from pygame import Rect, draw, font
from UI.button import Button
from windows.base_window import BaseWindow

class ProcessingViewport(BaseWindow):
    """Multi-mode viewport for pipeline/input/output/compare visualization"""
    def __init__(self, 
                 rel_pos=(0.251, 0.661), 
                 rel_size=(0.498, 0.338), 
                 reference_resolution=(1920, 1080), 
                 background_color=(30, 30, 30)):
        super().__init__(rel_pos,rel_size,reference_resolution,background_color)
        self.current_mode = "pipeline"
        self.pipeline_canvas = None
        self.input_images = []
        self.output_images = []
        self.current_input_index = 0
        self.current_output_index = 0
        self.mode_buttons = []
        return
    
    def set_pipeline_canvas(self, canvas):
        """Set the pipeline canvas for pipeline view"""
        self.pipeline_canvas = canvas
        return
    
    def set_input_images(self, images):
        """Set input images for preview"""
        self.input_images = images
        self.current_input_index = 0
        return
    
    def set_output_images(self, images):
        """Set output images for display"""
        self.output_images = images
        self.current_output_index = 0
        return
    
    def update_layout(self, window_size):
        """Update viewport size and position"""
        super().update_layout(window_size)
        for button in self.mode_buttons:
            button.update_layout(window_size)
        if self.pipeline_canvas:
            self.pipeline_canvas.update_layout(window_size)
        return
    
    def handle_events(self, events):
        """Handle events for viewport"""
        self.handle_resize_events(events)
        for button in self.mode_buttons:
            button.handle_events(events)
        if self.current_mode == "pipeline" and self.pipeline_canvas:
            self.pipeline_canvas.handle_events(events)
        return
    
    def update(self):
        """Update viewport state"""
        for button in self.mode_buttons:
            button.update()
        if self.current_mode == "pipeline" and self.pipeline_canvas:
            self.pipeline_canvas.update()
        return
    
    def draw(self, surface):
        """Draw viewport based on current mode"""
        draw.rect(surface, self.background_color, self.rect)
        draw.rect(surface, (100, 100, 100), self.rect, 2)
        clip_rect = surface.get_clip()
        surface.set_clip(self.rect)
        if self.current_mode == "pipeline":
            self._draw_pipeline_view(surface, self.rect)
        elif self.current_mode == "input":
            self._draw_input_view(surface, self.rect)
        elif self.current_mode == "output":
            self._draw_output_view(surface, self.rect)
        elif self.current_mode == "compare":
            self._draw_compare_view(surface, self.rect)
        surface.set_clip(clip_rect)
        return
    
    def _draw_pipeline_view(self, surface, content_rect):
        """Draw pipeline node canvas"""
        if self.pipeline_canvas:
            old_rect = self.pipeline_canvas.rect
            self.pipeline_canvas.rect = content_rect
            self.pipeline_canvas.draw(surface)
            self.pipeline_canvas.rect = old_rect
        else:
            text = self.font.render("No Pipeline Loaded", True, (150, 150, 150))
            text_rect = text.get_rect(center=content_rect.center)
            surface.blit(text, text_rect)
        return
    
    def _draw_input_view(self, surface, content_rect):
        """Draw input image preview"""
        if not self.input_images:
            text = self.font.render("No Input Images", True, (150, 150, 150))
            text_rect = text.get_rect(center=content_rect.center)
            surface.blit(text, text_rect)
            return
        
        img = self.input_images[self.current_input_index]
        self._draw_scaled_image(surface, img, content_rect)
        if len(self.input_images) > 1:
            counter_text = f"{self.current_input_index + 1} / {len(self.input_images)}"
            text = self.font.render(counter_text, True, (255, 255, 255))
            surface.blit(text, (content_rect.x + 10, content_rect.y + 10))
        return
    
    def _draw_output_view(self, surface, content_rect):
        """Draw output image"""
        if not self.output_images:
            text = self.font.render("No Output Yet", True, (150, 150, 150))
            text_rect = text.get_rect(center=content_rect.center)
            surface.blit(text, text_rect)
            return
        img = self.output_images[self.current_output_index]
        self._draw_scaled_image(surface, img, content_rect)
        if len(self.output_images) > 1:
            counter_text = f"{self.current_output_index + 1} / {len(self.output_images)}"
            text = self.font.render(counter_text, True, (255, 255, 255))
            surface.blit(text, (content_rect.x + 10, content_rect.y + 10))
        return
    
    def _draw_compare_view(self, surface, content_rect):
        """Draw side-by-side input and output comparison"""
        if not self.input_images or not self.output_images:
            text = self.font.render("Need Input and Output", True, (150, 150, 150))
            text_rect = text.get_rect(center=content_rect.center)
            surface.blit(text, text_rect)
            return
        left_rect = Rect(content_rect.x, content_rect.y, 
                        content_rect.width // 2 - 2, content_rect.height)
        right_rect = Rect(content_rect.x + content_rect.width // 2 + 2, content_rect.y,
                         content_rect.width // 2 - 2, content_rect.height)
        input_img = self.input_images[min(self.current_input_index, len(self.input_images) - 1)]
        self._draw_scaled_image(surface, input_img, left_rect)
        output_img = self.output_images[min(self.current_output_index, len(self.output_images) - 1)]
        self._draw_scaled_image(surface, output_img, right_rect)
        input_label = self.font.render("Input", True, (255, 255, 255))
        output_label = self.font.render("Output", True, (255, 255, 255))
        surface.blit(input_label, (left_rect.x + 10, left_rect.y + 10))
        surface.blit(output_label, (right_rect.x + 10, right_rect.y + 10))
        return
    
    def _draw_scaled_image(self, surface, img, rect):
        """Draw an image scaled to fit within rect"""
        if img is None:
            return
        img_width, img_height = img.get_size()
        scale_x = rect.width / img_width
        scale_y = rect.height / img_height
        scale = min(scale_x, scale_y)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        from pygame import transform
        scaled_img = transform.smoothscale(img, (new_width, new_height))
        x_offset = (rect.width - new_width) // 2
        y_offset = (rect.height - new_height) // 2
        surface.blit(scaled_img, (rect.x + x_offset, rect.y + y_offset))
        return