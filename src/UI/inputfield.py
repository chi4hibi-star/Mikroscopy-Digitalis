from pygame import draw, font, MOUSEBUTTONDOWN, KEYDOWN, key, K_BACKSPACE, K_RETURN
from UI.base_ui import BaseUI
from typing import Optional, Tuple, Literal, Any, Callable

class InputField(BaseUI):
    # Constants
    MIN_FONT_SIZE = 8
    FONT_HEIGHT_RATIO = 0.4
    MAX_FONT_HEIGHT_RATIO = 0.6
    PADDING_RATIO = 0.15
    MIN_PADDING = 5
    BORDER_RADIUS = 5
    
    def __init__(self,
                 rel_pos: Tuple[float, float] = (0, 0),
                 rel_size: Optional[Tuple[float, float]] = None,
                 s_font: Optional[font.Font] = None,
                 fontsize: int = 32,
                 input_type: Literal["all", "numbers", "letters", "key"] = "all",
                 color_active: Tuple[int, int, int] = (200, 200, 200),
                 color_inactive: Tuple[int, int, int] = (100, 100, 100),
                 start_text: Optional[str] = None,
                 text_color: Tuple[int, int, int] = (0, 0, 0),
                 linked_element: Optional[Any] = None,
                 reference_resolution: Tuple[int, int] = (1920, 1080)) -> None:
        """
        Initialize the InputField
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            s_font: Custom pygame font (if None, uses system font)
            fontsize: Base font size
            input_type: Type of input ("all", "numbers", "letters", "key")
            color_active: RGB color when active/focused
            color_inactive: RGB color when inactive
            start_text: Initial text content
            text_color: RGB color for the text
            linked_element: UI element to sync values with (e.g., Slider)
            reference_resolution: Reference resolution for scaling
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.input_type = input_type
        self.color_active = color_active
        self.color_inactive = color_inactive
        self.text_color = text_color
        self.s_font = s_font
        self.base_fontsize = fontsize
        self.fontsize = fontsize
        self.linked_element = linked_element
        self.font = s_font or font.SysFont(None,fontsize)
        self.text = start_text or ""
        self.padding = 8
        self.active = False
        self.select_all_on_next_input = False
        self.wait_key_input = False
        return

    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update input field size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        _, _, _, abs_height = self.calculate_absolute_rect(window_size)
        if not self.s_font:
            target_fontsize = int(abs_height * self.FONT_HEIGHT_RATIO)
            max_fontsize = int(abs_height * self.MAX_FONT_HEIGHT_RATIO)
            self.fontsize = max(self.MIN_FONT_SIZE, min(target_fontsize, max_fontsize))
            self.font = font.SysFont(None, self.fontsize)
            self.padding = max(self.MIN_PADDING, int(abs_height * self.PADDING_RATIO))
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
                self._handle_mouse_click(event)
            if self.active and event.type in (KEYDOWN, MOUSEBUTTONDOWN):
                self._handle_input(event)
        return
    
    def _handle_mouse_click(self, event) -> None:
        """
        Handle mouse click events
        
        Args:
            event: Pygame MOUSEBUTTONDOWN event
        """
        was_active = self.active
        self.active = self.rect.collidepoint(event.pos)
        if self.active and not was_active:
            self.await_key_input = (self.input_type == "key")
            self.select_all_on_next_input = True
        return
    
    def _handle_input(self, event) -> None:
        """
        Handle keyboard/mouse input when field is active
        
        Args:
            event: Pygame event (KEYDOWN or MOUSEBUTTONDOWN)
        """
        if self.select_all_on_next_input:
            self.text = ""
            self.select_all_on_next_input = False
        if self.input_type == "key" and self.await_key_input:
            self._capture_key(event)
            return
        if event.type == KEYDOWN:
            self._handle_keydown(event)
        return
    
    def _capture_key(self, event) -> None:
        """
        Capture key/mouse button for keybinding input
        
        Args:
            event: Pygame event
        """
        if event.type == MOUSEBUTTONDOWN:
            mouse_names = {1: "MOUSE_LEFT", 2: "MOUSE_MIDDLE", 3: "MOUSE_RIGHT"}
            self.text = mouse_names.get(event.button, f"MOUSE_{event.button}")
        elif event.type == KEYDOWN:
            self.text = key.name(event.key)
        self._update_linked_from_text()
        self.active = False
        self.await_key_input = False
        return
    
    def _handle_keydown(self, event) -> None:
        """
        Handle keyboard key press
        
        Args:
            event: Pygame KEYDOWN event
        """
        if event.key == K_BACKSPACE:
            self.text = self.text[:-1]
        elif event.key == K_RETURN:
            self._update_linked_from_text()
            self.active = False
        else:
            char = event.unicode
            if self._is_valid_char(char):
                self.text += char
        return
    
    def _is_valid_char(self, char: str) -> bool:
        """
        Check if character is valid for current input type
        
        Args:
            char: Character to validate
        
        Returns:
            True if character is valid
        """
        if self.input_type == "numbers":
            return char.isdigit() or char == "." or char == "-"
        elif self.input_type == "letters":
            return char.isalpha() or char == " "
        elif self.input_type == "all":
            return char.isprintable()
        return False

    def _update_linked_from_text(self)->None:
        """
        Update linked element's value from current text
        """
        if not self.linked_element:
            return
        try:
            if self.input_type == "numbers":
                value = float(self.text) if self.text else 0.0
            else:
                value = self.text
            if hasattr(self.linked_element, 'set_value'):
                self.linked_element.set_value(value)
        except ValueError:
            pass
        return
    
    def sync_from_linked(self)->None:
        """
        Synchronize text from linked element's value
        """
        if not self.linked_element or not hasattr(self.linked_element, 'get_value'):
            return
        val = self.linked_element.get_value()
        self.text = self._format_value(val)
        return
    
    def _format_value(self, val: Any) -> str:
        """
        Format a value for display as text
        
        Args:
            val: Value to format
        
        Returns:
            Formatted string
        """
        if isinstance(val, float):
            if abs(val) < 1:
                return f"{val:.2f}"
            elif abs(val) < 100:
                return f"{val:.1f}"
            else:
                return f"{int(val)}"
        elif isinstance(val, int):
            return str(val)
        else:
            return str(val)

    def link_to(self,other: Any) -> None:
        """
        Link this input field to another UI element
        
        Args:
            other: UI element to link to (must have get_value/set_value methods)
        """
        self.linked_element = other
        return
    
    def update(self):
        """
        Update the input field state (called every frame)
        Syncs from linked element when not active
        """
        if not self.active:
            self.sync_from_linked()
        else:
            self._update_linked_from_text()
        return

    def draw(self,surface):
        """
        Draw the input field to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        color = self.color_active if self.active else self.color_inactive
        draw.rect(surface, color, self.rect, border_radius=self.BORDER_RADIUS)
        self._draw_text(surface)
        return

    def _draw_text(self, surface) -> None:
        """
        Render and draw the text with overflow handling
        
        Args:
            surface: Pygame surface to draw on
        """
        txt_surf = self.font.render(self.text, True, self.text_color)
        max_width = self.rect.width - (2 * self.padding)
        if txt_surf.get_width() > max_width:
            visible_text = self.text
            while len(visible_text) > 0:
                txt_surf = self.font.render("..." + visible_text, True, self.text_color)
                if txt_surf.get_width() <= max_width:
                    break
                visible_text = visible_text[1:]
        text_x = self.rect.x + self.padding
        text_y = self.rect.y + (self.rect.height - txt_surf.get_height()) / 2
        surface.blit(txt_surf, (text_x, text_y))
        return
    
    def get_text(self) -> str:
        """
        Get the current text value
        
        Returns:
            Current text content
        """
        return self.text
    
    def set_text(self, new_text: str) -> None:
        """
        Set the text value
        
        Args:
            new_text: New text to display
        """
        self.text = new_text
        return
    
    def clear(self) -> None:
        """
        Clear the input field
        """
        self.text = ""
        if self.linked_element:
            self._update_linked_from_text()
        return