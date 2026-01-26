from pygame import draw, Rect, font, MOUSEBUTTONDOWN
from UI.base_ui import BaseUI
from typing import List, Optional, Tuple, Any

class DropdownMenu(BaseUI):
    #Constants
    MIN_FONT_SIZE = 8
    TRIANGLE_SIZE_RATIO = 0.25
    TEXT_PADDING = 5
    def __init__(self,
                 rel_pos:Tuple[float,float]=(0,0),
                 rel_size:Optional[Tuple[float,float]] = None,
                 options:Optional[List[Any]]=None,
                 s_font:Optional[font.Font]=None,
                 fontsize:int=32,
                 selected_index:int=0,
                 color_inactive:Tuple[int,int,int]=(100,100,100),
                 color_active:Tuple[int,int,int]=(150,150,150),
                 text_color:Tuple[int,int,int]=(0,0,0),
                 background_color:Tuple[int,int,int]=(200,200,200),
                 reference_resolution:Tuple[int,int]=(1920,1080)):
        """
        Initialize the DropdownMenu
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            options: List of options to display (default: empty list)
            s_font: Custom pygame font (if None, uses system font)
            fontsize: Base font size
            selected_index: Index of initially selected option
            color_inactive: RGB color for option items
            color_active: RGB color for highlighted option
            text_color: RGB color for text
            background_color: RGB color for main dropdown background
            reference_resolution: Reference resolution for scaling
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.options = options if options is not None else []
        self.selected_index = selected_index if selected_index < len(self.options) else 0
        self.s_font = s_font
        self.base_fontsize = fontsize
        self.fontsize = fontsize
        self.color_inactive = color_inactive
        self.color_active = color_active
        self.text_color = text_color
        self.background_color = background_color
        self.expanded = False
        self.font = s_font or font.SysFont(None,fontsize)
        self.option_rects = []
        return
    
    def update_layout(self, window_size:Tuple[int,int])->None:
        """
        Update dropdown menu size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        if not self.should_update_layout(window_size):
            return
        _, _, _, abs_height = self.calculate_absolute_rect(window_size)
        if not self.s_font:
            target_fontsize = int(abs_height * 0.65)
            self.fontsize = max(self.MIN_FONT_SIZE, min(target_fontsize, int(abs_height * 0.9)))
            self.font = font.SysFont(None, self.fontsize)
        self._update_option_rects()
        return

    def handle_events(self, events:list)->None:
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_event(events)
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
                    self.expanded = not self.expanded
                elif self.expanded:
                    for i, option_rect in enumerate(self.option_rects):
                        if option_rect.collidepoint(event.pos):
                            self.selected_index = i
                            self.expanded = False
                            break
                    else:
                        self.expanded = False
        return
    
    def update(self):
        """
        Update the dropdown menu state (called every frame)
        No per-frame updates needed
        """
        pass
            
    def draw(self, surface)->None:
        """
        Draw the dropdown menu to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        draw.rect(surface, self.background_color, self.rect)
        if self.options and 0 <= self.selected_index < len(self.options):
            text = str(self.options[self.selected_index])
        else:
            text = ""
        txt_surf = self.font.render(text, True, self.text_color)
        text_x = self.rect.x + self.TEXT_PADDING
        text_y = self.rect.y + (self.rect.height - txt_surf.get_height()) / 2
        surface.blit(txt_surf, (text_x, text_y))
        triangle_points = self._get_triangle_points()
        draw.polygon(surface, self.text_color, triangle_points)
        if self.expanded:
            for i,option in enumerate(self.options):
                if i < len(self.option_rects):
                    option_rect = self.option_rects[i]
                    draw.rect(surface,self.color_inactive,option_rect,border_radius=2)
                    option_text = self.font.render(str(option),True,self.text_color)
                    option_x = option_rect.x + self.TEXT_PADDING
                    option_y = option_rect.y + (option_rect.height-option_text.get_height())/2
                    surface.blit(option_text,(option_x,option_y))
        return
    
    def _get_triangle_points(self)->List[Tuple[float,float]]:
        '''
        Calculate triangle points for dropdown indicator
        
        Returns:
            List of 3 points forming the triangle
        '''
        triangle_center_x = self.rect.x + self.rect.width - 15
        triangle_center_y = self.rect.y + self.rect.height/2
        tri_size = min(6,self.rect.height*self.TRIANGLE_SIZE_RATIO)
        if self.expanded:
            return [
                (triangle_center_x, triangle_center_y - tri_size),
                (triangle_center_x - tri_size, triangle_center_y + tri_size),
                (triangle_center_x + tri_size, triangle_center_y + tri_size)
            ]
        else:
            return [
                (triangle_center_x, triangle_center_y + tri_size),
                (triangle_center_x - tri_size, triangle_center_y - tri_size),
                (triangle_center_x + tri_size, triangle_center_y - tri_size)
            ]

    def _update_option_rects(self)->None:
        """
        Update the rectangles for dropdown options based on current rect
        """
        self.option_rects = []
        for i in range(len(self.options)):
            option_rect = Rect(
                self.rect.x,
                self.rect.y + (i + 1) * self.rect.height,
                self.rect.width,
                self.rect.height
            )
            self.option_rects.append(option_rect)
        return
    
    def set_options(self, options:List[Any], selected_index:int=0)->None:
        """
        Update the list of options
        
        Args:
            options: New list of options
            selected_index: Index to select (default: 0)
        """
        self.options = options
        self.selected_index = selected_index if selected_index < len(options) else 0
        self._update_option_rects()
        return
    
    def get_selected(self)->Optional[Any]:
        """
        Get the currently selected option
        
        Returns:
            The selected option value, or None if no options
        """
        if self.options and 0 <= self.selected_index < len(self.options):
            return self.options[self.selected_index]
        return None
    
    def get_selected_index(self)->int:
        """
        Get the index of the currently selected option
        
        Returns:
            The selected index
        """
        return self.selected_index
    
    def set_selected_index(self, index:int)->None:
        """
        Set the selected option by index
        
        Args:
            index: Index to select
        """
        if 0 <= index < len(self.options):
            self.selected_index = index
        return