from pygame import draw, Rect, font, MOUSEBUTTONDOWN
from UI.base_ui import BaseUI
from typing import List, Optional, Tuple, Any, Literal, Callable

class RadioButtonGroup(BaseUI):
    MIN_FONT_SIZE = 8
    FONT_HEIGHT_RATIO = 0.5
    CIRCLE_RADIUS_RATIO = 0.3
    INNER_CIRCLE_RATIO = 0.6
    TEXT_OFFSET_RATIO = 1.5
    BUTTON_SPACING_RATIO = 0.05
    BORDER_RADIUS = 5
    
    def __init__(self,
                 rel_pos: Tuple[float, float] = (0, 0),
                 rel_size: Tuple[float, float] = (0.3, 0.05),
                 options: Optional[List[Any]] = None,
                 selected_index: int = 0,
                 layout: Literal["horizontal", "vertical"] = "horizontal",
                 shape: Optional[Tuple[int, int]] = None,
                 s_font: Optional[font.Font] = None,
                 fontsize: int = 32,
                 text_color: Tuple[int, int, int] = (255, 255, 255),
                 circle_color: Tuple[int, int, int] = (200, 200, 200),
                 selected_color: Tuple[int, int, int] = (0, 200, 0),
                 background_color: Optional[Tuple[int, int, int]] = None,
                 on_change_callback: Optional[Callable[[int, Any], None]] = None,
                 reference_resolution: Tuple[int, int] = (1920, 1080)) -> None:
        """
        Initialize the RadioButtonGroup
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            options: List of options to display
            selected_index: Index of initially selected option
            layout: "horizontal" or "vertical" - ignored if shape is provided
            shape: Tuple (rows, cols) for 2D grid layout, e.g., (2, 2) for 2x2 grid
                   If None, uses layout parameter
            s_font: Custom pygame font (if None, uses system font)
            fontsize: Base font size
            text_color: RGB color for text
            circle_color: RGB color for unselected circles
            selected_color: RGB color for selected circle (inner dot)
            background_color: RGB color for background (None for transparent)
            on_change_callback: Callback function(index, value) when selection changes
            reference_resolution: Reference resolution for scaling
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.options = options if options is not None else []
        self.selected_index = selected_index if selected_index < len(self.options) else 0
        self.layout = layout
        self.shape = shape
        self.s_font = s_font
        self.base_fontsize = fontsize
        self.fontsize = fontsize
        self.text_color = text_color
        self.circle_color = circle_color
        self.selected_color = selected_color
        self.background_color = background_color
        self.on_change_callback = on_change_callback
        self.font = s_font or font.SysFont(None, fontsize)
        self.button_rects = []
        self.circle_positions = []
        self.text_positions = []
        self.outer_radius = 10
        self.inner_radius = 6
    
    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update radio button group size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        _, _, _, abs_height = self.calculate_absolute_rect(window_size)
        if not self.s_font:
            target_fontsize = int(abs_height * self.FONT_HEIGHT_RATIO)
            self.fontsize = max(self.MIN_FONT_SIZE, target_fontsize)
            self.font = font.SysFont(None, self.fontsize)
        if self.shape:
            cell_height = abs_height / self.shape[0]
            self.outer_radius = int(cell_height * self.CIRCLE_RADIUS_RATIO)
        else:
            self.outer_radius = int(abs_height * self.CIRCLE_RADIUS_RATIO)
        
        self.inner_radius = int(self.outer_radius * self.INNER_CIRCLE_RATIO)
        self._calculate_button_positions()
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
                self._handle_click(event.pos)
        return
    
    def update(self) -> None:
        """
        Update the radio button group state (called every frame)
        No per-frame updates needed
        """
        pass
    
    def draw(self, surface) -> None:
        """
        Draw the radio button group to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        if self.background_color is not None:
            draw.rect(surface, self.background_color, self.rect, border_radius=self.BORDER_RADIUS)
        for i in range(len(self.options)):
            if i >= len(self.circle_positions):
                continue
            circle_pos = self.circle_positions[i]
            text_pos = self.text_positions[i]
            draw.circle(surface, self.circle_color, circle_pos, self.outer_radius, 2)
            if i == self.selected_index:
                draw.circle(surface, self.selected_color, circle_pos, self.inner_radius)
            text_surf = self.font.render(str(self.options[i]), True, self.text_color)
            surface.blit(text_surf, text_pos)
        return
    
    def _calculate_button_positions(self) -> None:
        """
        Calculate positions for all buttons based on layout or shape
        """
        self.button_rects = []
        self.circle_positions = []
        self.text_positions = []
        if not self.options:
            return
        if self.shape:
            self._calculate_grid_layout()
        elif self.layout == "horizontal":
            self._calculate_horizontal_layout()
        else:
            self._calculate_vertical_layout()
        return
    
    def _calculate_grid_layout(self) -> None:
        """
        Calculate button positions for 2D grid layout
        """
        rows, cols = self.shape
        cell_width = self.rect.width / cols
        cell_height = self.rect.height / rows
        for i, option in enumerate(self.options):
            row = i // cols
            col = i % cols
            if row >= rows:
                break
            circle_x = int(self.rect.x + col * cell_width + self.outer_radius + 5)
            circle_y = int(self.rect.y + row * cell_height + cell_height / 2)
            self.circle_positions.append((circle_x, circle_y))
            text_surf = self.font.render(str(option), True, self.text_color)
            text_x = circle_x + self.outer_radius + int(self.outer_radius * self.TEXT_OFFSET_RATIO)
            text_y = circle_y - text_surf.get_height() // 2
            self.text_positions.append((text_x, text_y))
            button_rect = Rect(
                int(self.rect.x + col * cell_width),
                int(self.rect.y + row * cell_height),
                int(cell_width),
                int(cell_height)
            )
            self.button_rects.append(button_rect)
        return
    
    def _calculate_horizontal_layout(self) -> None:
        """
        Calculate button positions for horizontal layout
        """
        num_buttons = len(self.options)
        if num_buttons == 0:
            return
        total_text_width = 0
        for option in self.options:
            text_surf = self.font.render(str(option), True, self.text_color)
            total_text_width += text_surf.get_width()
        total_circle_space = num_buttons * (self.outer_radius * 2)
        total_text_space = total_text_width + num_buttons * int(self.outer_radius * self.TEXT_OFFSET_RATIO)
        total_needed = total_circle_space + total_text_space
        if num_buttons > 1:
            spacing = max(10, int((self.rect.width - total_needed) / (num_buttons - 1)))
        else:
            spacing = 0
        current_x = self.rect.x + self.outer_radius
        for i, option in enumerate(self.options):
            circle_x = current_x
            circle_y = self.rect.centery
            self.circle_positions.append((circle_x, circle_y))
            text_surf = self.font.render(str(option), True, self.text_color)
            text_x = circle_x + self.outer_radius + int(self.outer_radius * self.TEXT_OFFSET_RATIO)
            text_y = circle_y - text_surf.get_height() // 2
            self.text_positions.append((text_x, text_y))
            button_width = self.outer_radius * 2 + int(self.outer_radius * self.TEXT_OFFSET_RATIO) + text_surf.get_width()
            button_rect = Rect(
                circle_x - self.outer_radius,
                self.rect.y,
                button_width,
                self.rect.height
            )
            self.button_rects.append(button_rect)
            current_x += button_width + spacing
        return
    
    def _calculate_vertical_layout(self) -> None:
        """
        Calculate button positions for vertical layout
        """
        num_buttons = len(self.options)
        if num_buttons == 0:
            return
        button_height = self.rect.height / num_buttons
        for i, option in enumerate(self.options):
            circle_x = self.rect.x + self.outer_radius + 5
            circle_y = int(self.rect.y + i * button_height + button_height / 2)
            self.circle_positions.append((circle_x, circle_y))
            text_surf = self.font.render(str(option), True, self.text_color)
            text_x = circle_x + self.outer_radius + int(self.outer_radius * self.TEXT_OFFSET_RATIO)
            text_y = circle_y - text_surf.get_height() // 2
            self.text_positions.append((text_x, text_y))
            button_rect = Rect(
                self.rect.x,
                int(self.rect.y + i * button_height),
                self.rect.width,
                int(button_height)
            )
            self.button_rects.append(button_rect)
        return
    
    def _handle_click(self, pos: Tuple[int, int]) -> None:
        """
        Handle mouse click on buttons
        
        Args:
            pos: Mouse position (x, y)
        """
        for i, button_rect in enumerate(self.button_rects):
            if button_rect.collidepoint(pos):
                if i != self.selected_index:
                    self.selected_index = i
                    if self.on_change_callback:
                        self.on_change_callback(i, self.options[i])
                break
        return
    
    def get_selected(self) -> Optional[Any]:
        """
        Get the currently selected option
        
        Returns:
            The selected option value, or None if no options
        """
        if self.options and 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return None
    
    def get_selected_index(self) -> int:
        """
        Get the index of the currently selected option
        
        Returns:
            The selected index
        """
        return self.selected_index
    
    def set_selected_index(self, index: int) -> None:
        """
        Set the selected option by index
        
        Args:
            index: Index to select
        """
        if 0 <= index < len(self.options):
            old_index = self.selected_index
            self.selected_index = index
            if old_index != index and self.on_change_callback:
                self.on_change_callback(index, self.options[index])
        return
    
    def set_options(self, options: List[Any], selected_index: int = 0) -> None:
        """
        Update the list of options
        
        Args:
            options: New list of options
            selected_index: Index to select (default: 0)
        """
        self.options = options
        self.selected_index = selected_index if selected_index < len(options) else 0
        self._calculate_button_positions()
        return
    
    def set_shape(self, shape: Optional[Tuple[int, int]]) -> None:
        """
        Update the grid shape
        
        Args:
            shape: New shape (rows, cols) or None for layout-based positioning
        """
        self.shape = shape
        self._calculate_button_positions()
        return