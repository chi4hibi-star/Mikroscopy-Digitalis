from pygame import Rect, draw, font, MOUSEWHEEL
from windows.base_window import BaseWindow
from UI.label import Label
from UI.slider import Slider
from UI.inputfield import InputField
from UI.dropdownmenu import DropdownMenu
from UI.button import Button

class ParameterPanel(BaseWindow):
    def __init__(self,
                 rel_pos=(0.251, 0.661),
                 rel_size=(0.498, 0.338),
                 reference_resolution=(1920, 1080),
                 background_color=(40, 40, 40),
                 header_color=(60, 60, 60),
                 text_color=(255, 255, 255),
                 param_bg_color=(50, 50, 50)):
        super().__init__(rel_pos, rel_size, reference_resolution, background_color)
        self.base_header_font_size = 24
        self.header_color = header_color
        self.text_color = text_color
        self.param_bg_color = param_bg_color
        self.base_header_height = 50
        self.header_height = 50
        self.base_param_height = 60
        self.param_height = 60
        self.base_param_spacing = 10
        self.param_spacing = 10
        self.selected_node = None
        self.selected_node_name = ""
        self.parameters = []
        self.param_widgets = []
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 30
        self.header_font = None
        return
    
    def update_layout(self, window_size):
        super().update_layout(window_size)
        scale_factor = self.get_scale_factor()
        self.font_size = max(16, int(self.base_font_size * scale_factor))
        self.font = font.SysFont(None, self.font_size)
        self.header_font_size = max(20, int(self.base_header_font_size * scale_factor))
        self.header_font = font.SysFont(None, self.header_font_size)
        self.header_height = max(40, int(self.base_header_height * scale_factor))
        self.param_height = max(50, int(self.base_param_height * scale_factor))
        self.param_spacing = max(5, int(self.base_param_spacing * scale_factor))
        self._rebuild_widgets()
        return
    
    def handle_events(self, events):
        self.handle_resize_events(events)
        for event in events:
            if event.type == MOUSEWHEEL:
                if self.rect.collidepoint(event.pos) if hasattr(event, 'pos') else True:
                    old_offset = self.scroll_offset
                    self.scroll_offset -= event.y * self.scroll_speed
                    self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
                    if old_offset != self.scroll_offset:
                        self._rebuild_widgets()
        for widget in self.param_widgets:
            widget.handle_events(events)
        return
    
    def update(self):
        for widget in self.param_widgets:
            widget.update()
        if self.selected_node:
            for widget in self.param_widgets:
                if hasattr(widget, '_param_name'):
                    param_name = widget._param_name
                    for param in self.parameters:
                        if param['name'] == param_name:
                            if hasattr(widget, 'get_value'):
                                current_value = widget.get_value()
                                if param['type'] == 'int':
                                    self.selected_node.parameters[param_name] = int(current_value)
                                elif param['type'] == 'float':
                                    self.selected_node.parameters[param_name] = float(current_value)
                                elif param['type'] == 'bool':
                                    self.selected_node.parameters[param_name] = bool(current_value)
                            elif hasattr(widget, 'get_selected'):
                                self.selected_node.parameters[param_name] = widget.get_selected()
                            break
        return
    
    def draw(self, surface):
        draw.rect(surface, self.background_color, self.rect)
        draw.rect(surface, (100, 100, 100), self.rect, 2)
        header_rect = Rect(self.rect.x, self.rect.y, self.rect.width, self.header_height)
        draw.rect(surface, self.header_color, header_rect)
        if self.selected_node_name:
            header_text = self.header_font.render(self.selected_node_name, True, self.text_color)
        else:
            header_text = self.header_font.render("No Node Selected", True, (150, 150, 150))
        text_rect = header_text.get_rect(center=header_rect.center)
        surface.blit(header_text, text_rect)
        if not self.selected_node or not self.parameters:
            return
        content_rect = Rect(
            self.rect.x,
            self.rect.y + self.header_height,
            self.rect.width,
            self.rect.height - self.header_height
        )
        clip_rect = surface.get_clip()
        surface.set_clip(content_rect)
        for widget in self.param_widgets:
            widget.draw(surface)
        surface.set_clip(clip_rect)
        if self.max_scroll > 0:
            scrollbar_height = max(20, int(content_rect.height * 
                                         (content_rect.height / (len(self.parameters) * 
                                         (self.param_height + self.param_spacing)))))
            scrollbar_y = content_rect.y + int((self.scroll_offset / self.max_scroll) * 
                                              (content_rect.height - scrollbar_height))
            scrollbar_rect = Rect(
                self.rect.right - 10,
                scrollbar_y,
                8,
                scrollbar_height
            )
            draw.rect(surface, (150, 150, 150), scrollbar_rect, border_radius=4)
        return
    
    def set_selected_node(self, node, node_name, parameters):
        """
        Set the selected node and its parameters
        
        Args:
            node: The selected node object
            node_name: Name of the node
            parameters: List of parameter definitions
        """
        self.selected_node = node
        self.selected_node_name = node_name
        self.parameters = parameters
        for widget in self.param_widgets:
            if hasattr(widget, '_grid_managed'):
                widget._grid_managed = False
        self.param_widgets = []
        self.scroll_offset = 0
        if self.current_window_size:
            self._rebuild_widgets()
        return
    
    def clear_selection(self):
        self.selected_node = None
        self.selected_node_name = ""
        self.parameters = []
        self.param_widgets = []
        self.scroll_offset = 0
        self.max_scroll = 0
        return
    
    def _rebuild_widgets(self):
        if not self.rect.width or not self.rect.height or not self.parameters:
            return
        self.param_widgets = []
        content_y = self.rect.y + self.header_height + self.param_spacing - self.scroll_offset
        content_width = self.rect.width - 20
        padding_left = 10
        label_width_ratio = 0.30
        slider_width_ratio = 0.45
        input_width_ratio = 0.20
        gap = 5
        label_width = int(content_width * label_width_ratio)
        slider_width = int(content_width * slider_width_ratio)
        input_width = int(content_width * input_width_ratio)
        widget_height = int(self.param_height * 0.5)
        
        for param in self.parameters:
            param_name = param['name']
            param_type = param['type']
            param_value = param['value']
            label_rect = Rect(
                self.rect.x + padding_left,
                content_y,
                label_width,
                widget_height
            )
            widget_x = self.rect.x + padding_left + label_width + gap
            widget_rect = Rect(
                widget_x,
                content_y,
                slider_width,
                widget_height
            )
            label = Label(
                rel_pos=(0, 0),
                rel_size=(0.1, 0.05),
                text=param_name,
                text_color=self.text_color,
                background_color=None,
                reference_resolution=self.reference_resolution
            )
            label.rect = label_rect
            label._grid_managed = True
            label.current_window_size = self.current_window_size
            self.param_widgets.append(label)
            if param_type == 'int':
                min_val = param.get('min', 0)
                max_val = param.get('max', 100)
                slider = Slider(
                    rel_pos=(0, 0),
                    rel_size=(0.1, 0.03),
                    min_val=min_val,
                    max_val=max_val,
                    start_val=param_value,
                    color=(100, 150, 200),
                    background_color=(60, 60, 60),
                    handle_color=(255, 255, 255),
                    reference_resolution=self.reference_resolution
                )
                slider.rect = widget_rect
                slider._grid_managed = True
                slider.current_window_size = self.current_window_size
                slider._param_name = param_name
                self.param_widgets.append(slider)
                input_rect = Rect(
                    widget_x + slider_width + gap,
                    content_y,
                    input_width,
                    widget_height
                )
                input_field = InputField(
                    rel_pos=(0, 0),
                    rel_size=(0.05, 0.03),
                    input_type="numbers",
                    start_text=str(param_value),
                    color_active=(200, 200, 200),
                    color_inactive=(100, 100, 100),
                    text_color=(0, 0, 0),
                    reference_resolution=self.reference_resolution
                )
                input_field.rect = input_rect
                input_field._grid_managed = True
                input_field.current_window_size = self.current_window_size
                input_field._param_name = param_name
                input_field.link_to(slider)
                self.param_widgets.append(input_field)
            elif param_type == 'float':
                min_val = param.get('min', 0.0)
                max_val = param.get('max', 10.0)
                slider = Slider(
                    rel_pos=(0, 0),
                    rel_size=(0.1, 0.03),
                    min_val=min_val,
                    max_val=max_val,
                    start_val=param_value,
                    color=(100, 150, 200),
                    background_color=(60, 60, 60),
                    handle_color=(255, 255, 255),
                    reference_resolution=self.reference_resolution
                )
                slider.rect = widget_rect
                slider._grid_managed = True
                slider.current_window_size = self.current_window_size
                slider._param_name = param_name
                self.param_widgets.append(slider)
                input_rect = Rect(
                    widget_x + slider_width + gap,
                    content_y,
                    input_width,
                    widget_height
                )
                input_field = InputField(
                    rel_pos=(0, 0),
                    rel_size=(0.05, 0.03),
                    input_type="numbers",
                    start_text=f"{param_value:.2f}",
                    color_active=(200, 200, 200),
                    color_inactive=(100, 100, 100),
                    text_color=(0, 0, 0),
                    reference_resolution=self.reference_resolution
                )
                input_field.rect = input_rect
                input_field._grid_managed = True
                input_field.current_window_size = self.current_window_size
                input_field._param_name = param_name
                input_field.link_to(slider)
                self.param_widgets.append(input_field)
            elif param_type == 'bool':
                full_width_rect = Rect(
                    widget_x,
                    content_y,
                    slider_width + gap + input_width,
                    widget_height
                )
                button = Button(
                    text="True" if param_value else "False",
                    rel_pos=(0, 0),
                    rel_size=(0.1, 0.05),
                    callback=lambda pn=param_name: self._toggle_bool_param(pn),
                    base_color=(70, 150, 70) if param_value else (150, 70, 70),
                    hover_color=(90, 170, 90) if param_value else (170, 90, 90),
                    text_color=(255, 255, 255),
                    reference_resolution=self.reference_resolution
                )
                button.rect = full_width_rect
                button._grid_managed = True
                button.current_window_size = self.current_window_size
                button._param_name = param_name
                self.param_widgets.append(button)
            elif param_type == 'choice':
                options = param.get('options', [])
                selected_index = options.index(param_value) if param_value in options else 0
                full_width_rect = Rect(
                    widget_x,
                    content_y,
                    slider_width + gap + input_width,
                    widget_height
                )
                dropdown = DropdownMenu(
                    rel_pos=(0, 0),
                    rel_size=(0.1, 0.03),
                    options=options,
                    selected_index=selected_index,
                    color_inactive=(100, 100, 100),
                    color_active=(150, 150, 150),
                    text_color=(0, 0, 0),
                    background_color=(200, 200, 200),
                    reference_resolution=self.reference_resolution
                )
                dropdown.rect = full_width_rect
                dropdown._grid_managed = True
                dropdown.current_window_size = self.current_window_size
                dropdown._param_name = param_name
                dropdown._update_option_rects()
                self.param_widgets.append(dropdown)
            content_y += self.param_height + self.param_spacing
        total_height = len(self.parameters) * (self.param_height + self.param_spacing)
        content_height = self.rect.height - self.header_height
        self.max_scroll = max(0, total_height - content_height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)
        return
    
    def _toggle_bool_param(self, param_name):
        for param in self.parameters:
            if param['name'] == param_name:
                param['value'] = not param['value']
                self._rebuild_widgets()
                break
        return