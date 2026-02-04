from pygame import Rect, draw, font, MOUSEWHEEL
from windows.base_window import BaseWindow
from UI.label import Label
from UI.slider import Slider
from UI.inputfield import InputField
from UI.dropdownmenu import DropdownMenu
from UI.button import Button
from typing import Optional, Tuple, List, Dict, Any, Callable

class ParameterWidget:
    """
    Container for a parameter's UI widgets
    
    Attributes:
        param_name: Name of the parameter this widget controls
        param_type: Type of parameter ('int', 'float', 'bool', 'choice')
        widgets: List of UI components for this parameter
    """
    def __init__(self, param_name: str, param_type: str):
        self.param_name = param_name
        self.param_type = param_type
        self.widgets: List[Any] = []
        self._last_value: Any = None
        return
    
    def add_widget(self, widget: Any) -> None:
        """Add a UI widget to this parameter"""
        self.widgets.append(widget)
        return
    
    def get_value(self) -> Any:
        """Get the current value from the widget(s)"""
        if not self.widgets:
            return None
        main_widget = self.widgets[-1]
        if hasattr(main_widget, 'get_value'):
            return main_widget.get_value()
        elif hasattr(main_widget, 'get_selected'):
            return main_widget.get_selected()
        return None
    
    def has_changed(self) -> bool:
        """Check if value has changed since last check"""
        current = self.get_value()
        if current != self._last_value:
            self._last_value = current
            return True
        return False
    
    def handle_events(self, events: list) -> None:
        """Handle events for all widgets"""
        for widget in self.widgets:
            widget.handle_events(events)
        return
    
    def update(self) -> None:
        """Update all widgets"""
        for widget in self.widgets:
            widget.update()
        return
    
    def draw(self, surface) -> None:
        """Draw all widgets"""
        for widget in self.widgets:
            widget.draw(surface)
        return


class ParameterPanel(BaseWindow):
    """
    Panel for editing node parameters with scrollable content
    
    Features:
    - Dynamic widget generation based on parameter definitions
    - Support for int, float, bool, and choice parameter types
    - Scrollable content area for many parameters
    - Real-time syncing with selected node
    - Optimized updates (only sync changed values)
    """
    
    # Layout constants
    BASE_HEADER_HEIGHT = 50
    MIN_HEADER_HEIGHT = 40
    BASE_PARAM_HEIGHT = 60
    MIN_PARAM_HEIGHT = 50
    BASE_PARAM_SPACING = 10
    MIN_PARAM_SPACING = 5
    CONTENT_PADDING = 10
    
    # Widget layout ratios
    LABEL_WIDTH_RATIO = 0.30
    SLIDER_WIDTH_RATIO = 0.45
    INPUT_WIDTH_RATIO = 0.20
    WIDGET_GAP = 5
    WIDGET_HEIGHT_RATIO = 0.5
    
    # Font sizes
    BASE_HEADER_FONT_SIZE = 24
    MIN_HEADER_FONT_SIZE = 20
    
    # Scrolling
    SCROLL_SPEED = 30
    SCROLLBAR_WIDTH = 8
    SCROLLBAR_MARGIN = 10
    MIN_SCROLLBAR_HEIGHT = 20
    SCROLLBAR_COLOR = (150, 150, 150)
    SCROLLBAR_BORDER_RADIUS = 4
    
    # Colors
    NO_SELECTION_TEXT_COLOR = (150, 150, 150)
    BOOL_TRUE_COLOR = (70, 150, 70)
    BOOL_FALSE_COLOR = (150, 70, 70)
    BOOL_TRUE_HOVER = (90, 170, 90)
    BOOL_FALSE_HOVER = (170, 90, 90)
    
    def __init__(self,
                 rel_pos: Tuple[float, float] = (0.251, 0.661),
                 rel_size: Tuple[float, float] = (0.498, 0.338),
                 reference_resolution: Tuple[int, int] = (1920, 1080),
                 background_color: Tuple[int, int, int] = (40, 40, 40),
                 header_color: Tuple[int, int, int] = (60, 60, 60),
                 text_color: Tuple[int, int, int] = (255, 255, 255),
                 param_bg_color: Tuple[int, int, int] = (50, 50, 50)) -> None:
        """
        Initialize the ParameterPanel
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
            background_color: RGB color for background
            header_color: RGB color for header bar
            text_color: RGB color for text
            param_bg_color: RGB color for parameter backgrounds
        """
        super().__init__(rel_pos, rel_size, reference_resolution, background_color)
        self.header_color = header_color
        self.text_color = text_color
        self.param_bg_color = param_bg_color
        self.base_header_font_size = self.BASE_HEADER_FONT_SIZE
        self.header_height = self.BASE_HEADER_HEIGHT
        self.param_height = self.BASE_PARAM_HEIGHT
        self.param_spacing = self.BASE_PARAM_SPACING
        self.header_font: Optional[font.Font] = None
        self.selected_node: Optional[Any] = None
        self.selected_node_name: str = ""
        self.parameters: List[Dict[str, Any]] = []
        self.param_widgets: List[ParameterWidget] = []
        self.widget_factory: Dict[str, Callable] = {
            'int': self._create_int_widget,
            'float': self._create_float_widget,
            'bool': self._create_bool_widget,
            'choice': self._create_choice_widget
        }
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = self.SCROLL_SPEED
        self._content_rect_cache: Optional[Rect] = None
        return
    
    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update parameter panel size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        super().update_layout(window_size)
        scale_factor = self.get_scale_factor()
        self.font_size = max(16, int(self.base_font_size * scale_factor))
        self.font = font.SysFont(None, self.font_size)
        self.header_font_size = max(self.MIN_HEADER_FONT_SIZE, 
                                   int(self.base_header_font_size * scale_factor))
        self.header_font = font.SysFont(None, self.header_font_size)
        self.header_height = max(self.MIN_HEADER_HEIGHT, 
                                int(self.BASE_HEADER_HEIGHT * scale_factor))
        self.param_height = max(self.MIN_PARAM_HEIGHT, 
                               int(self.BASE_PARAM_HEIGHT * scale_factor))
        self.param_spacing = max(self.MIN_PARAM_SPACING, 
                                int(self.BASE_PARAM_SPACING * scale_factor))
        self._rebuild_widgets()
        self._content_rect_cache = self._calculate_content_rect()
        return
    
    def handle_events(self, events: list) -> None:
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_events(events)
        for event in events:
            if event.type == MOUSEWHEEL:
                self._handle_scroll(event)
        for param_widget in self.param_widgets:
            param_widget.handle_events(events)
        return
    
    def update(self) -> None:
        """Update the parameter panel state (called every frame)"""
        for param_widget in self.param_widgets:
            param_widget.update()
        if self.selected_node:
            self._sync_changed_parameters()
        return
    
    def draw(self, surface) -> None:
        """
        Draw the parameter panel to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        draw.rect(surface, self.background_color, self.rect)
        draw.rect(surface, (100, 100, 100), self.rect, 2)
        self._draw_header(surface)
        if self.selected_node and self.parameters:
            content_rect = self._content_rect_cache or self._calculate_content_rect()
            self._draw_parameters(surface, content_rect)
            self._draw_scrollbar(surface, content_rect)
        return
    
    def set_selected_node(self, node: Any, node_name: str, parameters: List[Dict[str, Any]]) -> None:
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
        for param_widget in self.param_widgets:
            for widget in param_widget.widgets:
                if hasattr(widget, '_grid_managed'):
                    widget._grid_managed = False
        self.param_widgets = []
        self.scroll_offset = 0
        if self.current_window_size:
            self._rebuild_widgets()
        return
    
    def clear_selection(self) -> None:
        """Clear the selected node and all parameters"""
        self.selected_node = None
        self.selected_node_name = ""
        self.parameters = []
        self.param_widgets = []
        self.scroll_offset = 0
        self.max_scroll = 0
        return
    
    def _handle_scroll(self, event) -> None:
        """
        Handle mouse wheel scrolling
        
        Args:
            event: Pygame MOUSEWHEEL event
        """
        if self.rect.collidepoint(event.pos) if hasattr(event, 'pos') else True:
            old_offset = self.scroll_offset
            self.scroll_offset -= event.y * self.scroll_speed
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            if old_offset != self.scroll_offset:
                self._update_widget_positions()
        return
    
    def _rebuild_widgets(self) -> None:
        """Rebuild all parameter widgets based on current parameters"""
        if not self.rect.width or not self.rect.height or not self.parameters:
            return
        self.param_widgets = []
        layout = self._calculate_widget_layout()
        content_rect = self._content_rect_cache or self._calculate_content_rect()
        y_offset = content_rect.y + self.param_spacing - self.scroll_offset
        for param in self.parameters:
            param_widget = self._create_parameter_widget(param, layout, y_offset)
            if param_widget:
                self.param_widgets.append(param_widget)
            y_offset += self.param_height + self.param_spacing
        self._update_scroll_limits(content_rect)
        return
    
    def _update_widget_positions(self) -> None:
        """Update widget positions after scroll (faster than full rebuild)"""
        content_rect = self._content_rect_cache or self._calculate_content_rect()
        y_offset = content_rect.y + self.param_spacing - self.scroll_offset
        for param_widget in self.param_widgets:
            for widget in param_widget.widgets:
                widget.rect.y = y_offset + (self.param_height - widget.rect.height) // 2
            y_offset += self.param_height + self.param_spacing
        return
    
    def _calculate_widget_layout(self) -> Dict[str, int]:
        """
        Calculate layout dimensions for widgets
        
        Returns:
            Dictionary with layout dimensions
        """
        content_width = self.rect.width - 2 * self.CONTENT_PADDING
        widget_height = int(self.param_height * self.WIDGET_HEIGHT_RATIO)
        return {
            'content_x': self.rect.x + self.CONTENT_PADDING,
            'content_width': content_width,
            'label_width': int(content_width * self.LABEL_WIDTH_RATIO),
            'slider_width': int(content_width * self.SLIDER_WIDTH_RATIO),
            'input_width': int(content_width * self.INPUT_WIDTH_RATIO),
            'widget_height': widget_height,
            'gap': self.WIDGET_GAP
        }
    
    def _create_parameter_widget(self, param: Dict[str, Any], layout: Dict[str, int], 
                                 y_offset: int) -> Optional[ParameterWidget]:
        """
        Create a parameter widget based on type
        
        Args:
            param: Parameter definition dictionary
            layout: Layout dimensions dictionary
            y_offset: Y position for this parameter
            
        Returns:
            ParameterWidget or None if type not supported
        """
        param_type = param.get('type')
        param_name = param.get('name')
        if param_type not in self.widget_factory:
            print(f"Warning: Unknown parameter type '{param_type}' for '{param_name}'")
            return None
        return self.widget_factory[param_type](param, layout, y_offset)
    
    def _create_int_widget(self, param: Dict[str, Any], layout: Dict[str, int], 
                          y_offset: int) -> ParameterWidget:
        """Create widgets for integer parameter"""
        param_widget = ParameterWidget(param['name'], 'int')
        label = self._create_label(param['name'], layout, y_offset)
        param_widget.add_widget(label)
        min_val = param.get('min', 0)
        max_val = param.get('max', 100)
        slider = self._create_slider(param['value'], min_val, max_val, layout, y_offset)
        slider._param_name = param['name']
        param_widget.add_widget(slider)
        input_field = self._create_input_field(str(param['value']), 'numbers', layout, y_offset, 
                                               is_input=True)
        input_field._param_name = param['name']
        input_field.link_to(slider)
        param_widget.add_widget(input_field)
        return param_widget
    
    def _create_float_widget(self, param: Dict[str, Any], layout: Dict[str, int], 
                            y_offset: int) -> ParameterWidget:
        """Create widgets for float parameter"""
        param_widget = ParameterWidget(param['name'], 'float')
        label = self._create_label(param['name'], layout, y_offset)
        param_widget.add_widget(label)
        min_val = param.get('min', 0.0)
        max_val = param.get('max', 10.0)
        slider = self._create_slider(param['value'], min_val, max_val, layout, y_offset)
        slider._param_name = param['name']
        param_widget.add_widget(slider)
        input_field = self._create_input_field(f"{param['value']:.2f}", 'numbers', layout, y_offset,
                                               is_input=True)
        input_field._param_name = param['name']
        input_field.link_to(slider)
        param_widget.add_widget(input_field)
        return param_widget
    
    def _create_bool_widget(self, param: Dict[str, Any], layout: Dict[str, int], 
                           y_offset: int) -> ParameterWidget:
        """Create widget for boolean parameter"""
        param_widget = ParameterWidget(param['name'], 'bool')
        label = self._create_label(param['name'], layout, y_offset)
        param_widget.add_widget(label)
        param_value = param['value']
        button_rect = Rect(
            layout['content_x'] + layout['label_width'] + layout['gap'],
            y_offset,
            layout['slider_width'] + layout['gap'] + layout['input_width'],
            layout['widget_height']
        )
        button = Button(
            text="True" if param_value else "False",
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            callback=lambda: self._toggle_bool_widget(param_widget),
            base_color=self.BOOL_TRUE_COLOR if param_value else self.BOOL_FALSE_COLOR,
            hover_color=self.BOOL_TRUE_HOVER if param_value else self.BOOL_FALSE_HOVER,
            text_color=(255, 255, 255),
            reference_resolution=self.reference_resolution
        )
        button.rect = button_rect
        button._grid_managed = True
        button.current_window_size = self.current_window_size
        button._param_name = param['name']
        button._param_value = param_value
        param_widget.add_widget(button)
        return param_widget
    
    def _create_choice_widget(self, param: Dict[str, Any], layout: Dict[str, int], 
                             y_offset: int) -> ParameterWidget:
        """Create widget for choice parameter"""
        param_widget = ParameterWidget(param['name'], 'choice')
        label = self._create_label(param['name'], layout, y_offset)
        param_widget.add_widget(label)
        options = param.get('options', [])
        selected_index = options.index(param['value']) if param['value'] in options else 0
        dropdown_rect = Rect(
            layout['content_x'] + layout['label_width'] + layout['gap'],
            y_offset,
            layout['slider_width'] + layout['gap'] + layout['input_width'],
            layout['widget_height']
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
        dropdown.rect = dropdown_rect
        dropdown._grid_managed = True
        dropdown.current_window_size = self.current_window_size
        dropdown._param_name = param['name']
        dropdown._update_option_rects()
        param_widget.add_widget(dropdown)
        return param_widget
    
    def _create_label(self, text: str, layout: Dict[str, int], y_offset: int) -> Label:
        """Create a label widget"""
        label_rect = Rect(
            layout['content_x'],
            y_offset,
            layout['label_width'],
            layout['widget_height']
        )
        label = Label(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.05),
            text=text,
            text_color=self.text_color,
            background_color=None,
            reference_resolution=self.reference_resolution
        )
        label.rect = label_rect
        label._grid_managed = True
        label.current_window_size = self.current_window_size
        return label
    
    def _create_slider(self, value: float, min_val: float, max_val: float, 
                      layout: Dict[str, int], y_offset: int) -> Slider:
        """Create a slider widget"""
        slider_rect = Rect(
            layout['content_x'] + layout['label_width'] + layout['gap'],
            y_offset,
            layout['slider_width'],
            layout['widget_height']
        )
        slider = Slider(
            rel_pos=(0, 0),
            rel_size=(0.1, 0.03),
            min_val=min_val,
            max_val=max_val,
            start_val=value,
            color=(100, 150, 200),
            background_color=(60, 60, 60),
            handle_color=(255, 255, 255),
            reference_resolution=self.reference_resolution
        )
        slider.rect = slider_rect
        slider._grid_managed = True
        slider.current_window_size = self.current_window_size
        return slider
    
    def _create_input_field(self, text: str, input_type: str, layout: Dict[str, int], 
                           y_offset: int, is_input: bool = False) -> InputField:
        """Create an input field widget"""
        x_offset = (layout['content_x'] + layout['label_width'] + 
                   layout['slider_width'] + 2 * layout['gap'])
        input_rect = Rect(
            x_offset,
            y_offset,
            layout['input_width'],
            layout['widget_height']
        )
        input_field = InputField(
            rel_pos=(0, 0),
            rel_size=(0.05, 0.03),
            input_type=input_type,
            start_text=text,
            color_active=(200, 200, 200),
            color_inactive=(100, 100, 100),
            text_color=(0, 0, 0),
            reference_resolution=self.reference_resolution
        )
        input_field.rect = input_rect
        input_field._grid_managed = True
        input_field.current_window_size = self.current_window_size
        return input_field
    
    def _sync_changed_parameters(self) -> None:
        """Sync only changed parameter values back to node (optimized)"""
        for param_widget in self.param_widgets:
            if param_widget.has_changed():
                param_name = param_widget.param_name
                value = param_widget.get_value()
                validated_value = self._validate_parameter_value(
                    param_name, value, param_widget.param_type
                )
                if validated_value is not None:
                    self.selected_node.parameters[param_name] = validated_value
        return
    
    def _validate_parameter_value(self, param_name: str, value: Any, 
                                  param_type: str) -> Optional[Any]:
        """
        Validate and convert parameter value
        
        Args:
            param_name: Name of the parameter
            value: Value to validate
            param_type: Type of parameter
            
        Returns:
            Validated value or None if invalid
        """
        try:
            if param_type == 'int':
                return int(value)
            elif param_type == 'float':
                return float(value)
            elif param_type == 'bool':
                return bool(value)
            else:
                return value
        except (ValueError, TypeError) as e:
            print(f"Invalid value for parameter '{param_name}': {value} ({e})")
            return None
    
    def _toggle_bool_widget(self, param_widget: ParameterWidget) -> None:
        """
        Toggle boolean parameter widget
        
        Args:
            param_widget: The boolean parameter widget to toggle
        """
        button = None
        for widget in param_widget.widgets:
            if isinstance(widget, Button):
                button = widget
                break
        if not button:
            return
        current_value = getattr(button, '_param_value', False)
        new_value = not current_value
        button._param_value = new_value
        button.set_text("True" if new_value else "False")
        button.base_color = self.BOOL_TRUE_COLOR if new_value else self.BOOL_FALSE_COLOR
        button.hover_color = self.BOOL_TRUE_HOVER if new_value else self.BOOL_FALSE_HOVER
        param_widget._last_value = None
        return
    
    def _draw_header(self, surface) -> None:
        """
        Draw the header bar
        
        Args:
            surface: Pygame surface to draw on
        """
        header_rect = Rect(self.rect.x, self.rect.y, self.rect.width, self.header_height)
        draw.rect(surface, self.header_color, header_rect)
        if self.selected_node_name:
            header_text = self.header_font.render(self.selected_node_name, True, self.text_color)
        else:
            header_text = self.header_font.render("No Node Selected", True, 
                                                  self.NO_SELECTION_TEXT_COLOR)
        
        text_rect = header_text.get_rect(center=header_rect.center)
        surface.blit(header_text, text_rect)
        return
    
    def _draw_parameters(self, surface, content_rect: Rect) -> None:
        """
        Draw all parameter widgets with clipping
        
        Args:
            surface: Pygame surface to draw on
            content_rect: Rectangle defining the content area
        """
        clip_rect = surface.get_clip()
        surface.set_clip(content_rect)
        for param_widget in self.param_widgets:
            param_widget.draw(surface)
        surface.set_clip(clip_rect)
        return
    
    def _draw_scrollbar(self, surface, content_rect: Rect) -> None:
        """
        Draw scrollbar if needed
        
        Args:
            surface: Pygame surface to draw on
            content_rect: Rectangle defining the content area
        """
        if self.max_scroll > 0:
            scrollbar_rect = self._calculate_scrollbar_rect(content_rect)
            if scrollbar_rect:
                draw.rect(surface, self.SCROLLBAR_COLOR, scrollbar_rect, 
                         border_radius=self.SCROLLBAR_BORDER_RADIUS)
        return
    
    def _calculate_content_rect(self) -> Rect:
        """
        Calculate the content area rectangle (below header)
        
        Returns:
            Rectangle defining the content area
        """
        return Rect(
            self.rect.x,
            self.rect.y + self.header_height,
            self.rect.width,
            self.rect.height - self.header_height
        )
    
    def _update_scroll_limits(self, content_rect: Rect) -> None:
        """
        Update scroll limits based on content height
        
        Args:
            content_rect: Rectangle defining the content area
        """
        total_height = len(self.parameters) * (self.param_height + self.param_spacing)
        content_height = content_rect.height
        self.max_scroll = max(0, total_height - content_height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)
        return
    
    def _calculate_scrollbar_rect(self, content_rect: Rect) -> Optional[Rect]:
        """
        Calculate scrollbar position and size
        
        Args:
            content_rect: Rectangle defining the content area
            
        Returns:
            Scrollbar rectangle or None if scrollbar not needed
        """
        if self.max_scroll <= 0:
            return None
        total_height = len(self.parameters) * (self.param_height + self.param_spacing)
        scrollbar_height = max(
            self.MIN_SCROLLBAR_HEIGHT,
            int(content_rect.height * (content_rect.height / total_height))
        )
        scroll_ratio = self.scroll_offset / self.max_scroll
        scrollbar_y = content_rect.y + int(scroll_ratio * (content_rect.height - scrollbar_height))
        return Rect(
            self.rect.right - self.SCROLLBAR_MARGIN,
            scrollbar_y,
            self.SCROLLBAR_WIDTH,
            scrollbar_height
        )