from pygame import Rect, draw, font, mouse, MOUSEBUTTONDOWN, MOUSEWHEEL, MOUSEMOTION
from windows.base_window import BaseWindow
from typing import Tuple, List, Optional, Dict

class NodeTemplate:
    """
    Represents a draggable node template in the library
    
    Attributes:
        name: Display name of the node
        category: Category this node belongs to
        description: Short description shown in the library
        color: RGB color tuple for visual identification
        rect: Pygame rect for positioning (updated during rendering)
        hovered: Whether mouse is currently hovering over this node
    """
    def __init__(self, name: str, category: str, description: str = "", color: Tuple[int, int, int] = (100, 150, 200)):
        self.name = name
        self.category = category
        self.description = description
        self.color = color
        self.rect = Rect(0, 0, 0, 0)
        self.hovered = False
        return
        
class TabbedNodeViewer(BaseWindow):
    """
    A tabbed viewer for browsing and dragging node templates
    
    Features:
    - Multiple categorized tabs for organizing nodes
    - Scrollable node list within each category
    - Drag-and-drop functionality
    - Visual feedback for hover states
    - Automatic scaling based on window size
    """
    
    # Visual constants
    MIN_TAB_HEIGHT = 30
    MIN_NODE_HEIGHT = 50
    MIN_NODE_PADDING = 5
    MIN_SCROLLBAR_HEIGHT = 20
    SCROLLBAR_WIDTH = 8
    SCROLLBAR_MARGIN = 10
    TAB_BORDER_WIDTH = 1
    NODE_BORDER_WIDTH = 2
    NODE_BORDER_RADIUS = 5
    NAME_TEXT_OFFSET = 8
    DESC_TEXT_OFFSET = 4
    DESC_FONT_SIZE_REDUCTION = 4
    MIN_DESC_FONT_SIZE = 12
    CONTENT_TOP_PADDING = 10
    
    # Color constants
    TAB_BORDER_COLOR = (80, 80, 80)
    NODE_BORDER_COLOR = (150, 150, 150)
    DESCRIPTION_TEXT_COLOR = (200, 200, 200)
    SCROLLBAR_COLOR = (150, 150, 150)
    SCROLLBAR_BORDER_RADIUS = 4
    
    def __init__(self,
                 rel_pos: Tuple[float, float] = (0.001, 0.051),
                 rel_size: Tuple[float, float] = (0.248, 0.948),
                 reference_resolution: Tuple[int, int] = (1920, 1080),
                 background_color: Tuple[int, int, int] = (40, 40, 40),
                 tab_color: Tuple[int, int, int] = (60, 60, 60),
                 tab_active_color: Tuple[int, int, int] = (80, 80, 80),
                 tab_hover_color: Tuple[int, int, int] = (70, 70, 70),
                 node_color: Tuple[int, int, int] = (100, 150, 200),
                 node_hover_color: Tuple[int, int, int] = (120, 170, 220),
                 text_color: Tuple[int, int, int] = (255, 255, 255)) -> None:
        """
        Initialize the TabbedNodeViewer
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
            background_color: RGB color for background
            tab_color: RGB color for inactive tabs
            tab_active_color: RGB color for active tab
            tab_hover_color: RGB color for hovered tab
            node_color: RGB color for nodes (default, can be overridden per node)
            node_hover_color: RGB color for hovered nodes
            text_color: RGB color for all text
        """
        super().__init__(rel_pos, rel_size, reference_resolution, background_color)
        
        # Color configuration
        self.tab_color = tab_color
        self.tab_active_color = tab_active_color
        self.tab_hover_color = tab_hover_color
        self.node_color = node_color
        self.node_hover_color = node_hover_color
        self.text_color = text_color
        
        # Scaled dimensions
        self.base_tab_height = 40
        self.tab_height = 40
        self.base_node_height = 60
        self.node_height = 60
        self.base_node_padding = 10
        self.node_padding = 10
        
        # Data structures
        self.categories: Dict[str, List[NodeTemplate]] = {}
        self.active_category: Optional[str] = None
        self.tab_rects: Dict[str, Rect] = {}
        self.nodes: List[NodeTemplate] = []
        self.visible_nodes: List[NodeTemplate] = []
        
        # Interaction state
        self.hovered_tab: Optional[str] = None
        self.hovered_node: Optional[NodeTemplate] = None
        self.dragging_node: Optional[NodeTemplate] = None
        self.drag_offset: Tuple[int, int] = (0, 0)
        
        # Scrolling state
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 30
        self.scroll_positions: Dict[str, int] = {}
        
        # Cache for optimization
        self._last_tab_calc: Optional[Tuple[int, int]] = None
        self._content_rect_cache: Optional[Rect] = None
        return
    
    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update tabbed node viewer size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        super().update_layout(window_size)
        scale_factor = self.get_scale_factor()
        self.tab_height = max(self.MIN_TAB_HEIGHT, int(self.base_tab_height * scale_factor))
        self.node_height = max(self.MIN_NODE_HEIGHT, int(self.base_node_height * scale_factor))
        self.node_padding = max(self.MIN_NODE_PADDING, int(self.base_node_padding * scale_factor))
        self._update_tab_rects()
        self._update_visible_nodes()
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
            elif event.type == MOUSEBUTTONDOWN:
                self._handle_mouse_down(event)
            elif event.type == MOUSEMOTION:
                if self.dragging_node:
                    pass
        return
    
    def update(self) -> None:
        """Update the tabbed node viewer state (called every frame)"""
        mouse_pos = mouse.get_pos()
        self._update_hovered_tab(mouse_pos)
        if not self.dragging_node:
            self._update_hovered_node(mouse_pos)
        return
    
    def draw(self, surface) -> None:
        """
        Draw the tabbed node viewer to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        draw.rect(surface, self.background_color, self.rect)
        draw.rect(surface, (100, 100, 100), self.rect, 2)
        self._draw_tabs(surface)
        content_rect = self._content_rect_cache or self._calculate_content_rect()
        self._draw_nodes(surface, content_rect)
        self._draw_scrollbar(surface, content_rect)
        return
    
    def add_category(self, category_name: str) -> None:
        """
        Add a new category tab
        
        Args:
            category_name: Name of the category to add
        """
        if category_name not in self.categories:
            self.categories[category_name] = []
            self.scroll_positions[category_name] = 0
            if self.active_category is None:
                self.active_category = category_name
            self._last_tab_calc = None
        return
    
    def add_node(self, name: str, category: str, description: str = "", color: Optional[Tuple[int, int, int]] = None) -> None:
        """
        Add a node template to a category
        
        Args:
            name: Node name
            category: Category this node belongs to
            description: Short description of the node
            color: Optional custom color (uses default node_color if None)
        """
        if category not in self.categories:
            self.add_category(category)
        node_color = color if color else self.node_color
        node = NodeTemplate(name, category, description, node_color)
        self.categories[category].append(node)
        self.nodes.append(node)
        if category == self.active_category:
            self._update_visible_nodes()
        return
    
    def get_dragging_node(self) -> Tuple[Optional[NodeTemplate], Optional[Tuple[int, int]]]:
        """
        Get the currently dragging node and mouse position
        
        Returns:
            Tuple of (dragging_node, mouse_position) or (None, None)
        """
        if self.dragging_node:
            mouse_pos = mouse.get_pos()
            return self.dragging_node, mouse_pos
        return None, None
    
    def stop_dragging(self) -> None:
        """Stop dragging the current node"""
        self.dragging_node = None
        return
    
    def _handle_scroll(self, event) -> None:
        """
        Handle mouse wheel scrolling
        
        Args:
            event: Pygame MOUSEWHEEL event
        """
        if self.rect.collidepoint(mouse.get_pos()):
            self.scroll_offset -= event.y * self.scroll_speed
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            if self.active_category:
                self.scroll_positions[self.active_category] = self.scroll_offset
        return
    
    def _handle_mouse_down(self, event) -> None:
        """
        Handle mouse button down event
        
        Args:
            event: Pygame MOUSEBUTTONDOWN event
        """
        if event.button != 1:
            return
        for category, tab_rect in self.tab_rects.items():
            if tab_rect.collidepoint(event.pos):
                self._switch_category(category)
                return
        content_rect = self._content_rect_cache or self._calculate_content_rect()
        if content_rect.collidepoint(event.pos):
            self._check_node_click(event.pos)
        return
    
    def _switch_category(self, category: str) -> None:
        """
        Switch to a different category tab
        
        Args:
            category: Category name to switch to
        """
        if category == self.active_category:
            return
        if self.active_category:
            self.scroll_positions[self.active_category] = self.scroll_offset
        self.active_category = category
        self._update_visible_nodes()
        self.scroll_offset = self.scroll_positions.get(category, 0)
        self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        return
    
    def _check_node_click(self, click_pos: Tuple[int, int]) -> None:
        """
        Check if a node was clicked and start dragging
        
        Args:
            click_pos: Mouse position where click occurred
        """
        content_rect = self._content_rect_cache or self._calculate_content_rect()
        y_offset = content_rect.y + self.CONTENT_TOP_PADDING - self.scroll_offset
        for node in self.visible_nodes:
            node_rect = Rect(
                self.rect.x + self.node_padding,
                y_offset,
                self.rect.width - 2 * self.node_padding,
                self.node_height
            )
            if node_rect.collidepoint(click_pos):
                self.dragging_node = node
                self.drag_offset = (
                    click_pos[0] - node_rect.x,
                    click_pos[1] - node_rect.y
                )
                break
            y_offset += self.node_height + self.node_padding
        return
    
    def _update_hovered_tab(self, mouse_pos: Tuple[int, int]) -> None:
        """
        Update which tab is currently hovered
        
        Args:
            mouse_pos: Current mouse position
        """
        self.hovered_tab = None
        for category, tab_rect in self.tab_rects.items():
            if tab_rect.collidepoint(mouse_pos):
                self.hovered_tab = category
                break
        return
    
    def _update_hovered_node(self, mouse_pos: Tuple[int, int]) -> None:
        """
        Update which node is currently hovered
        
        Args:
            mouse_pos: Current mouse position
        """
        self.hovered_node = None
        content_rect = self._content_rect_cache or self._calculate_content_rect()
        if not content_rect.collidepoint(mouse_pos):
            return
        y_offset = content_rect.y + self.CONTENT_TOP_PADDING - self.scroll_offset
        for node in self.visible_nodes:
            node_rect = Rect(
                self.rect.x + self.node_padding,
                y_offset,
                self.rect.width - 2 * self.node_padding,
                self.node_height
            )
            if node_rect.collidepoint(mouse_pos):
                self.hovered_node = node
                break
            y_offset += self.node_height + self.node_padding
        return
    
    def _update_tab_rects(self) -> None:
        """
        Update tab rectangles (with caching optimization)
        """
        if (self._last_tab_calc is not None and 
            self._last_tab_calc == (len(self.categories), self.rect.width)):
            return
        self.tab_rects = {}
        if not self.categories:
            return
        num_tabs = len(self.categories)
        tab_width = self.rect.width / num_tabs
        for i, category in enumerate(self.categories.keys()):
            tab_x = self.rect.x + i * tab_width
            tab_rect = Rect(tab_x, self.rect.y, tab_width, self.tab_height)
            self.tab_rects[category] = tab_rect
        self._last_tab_calc = (len(self.categories), self.rect.width)
        return
    
    def _update_visible_nodes(self) -> None:
        """
        Update the list of visible nodes for the active category
        """
        if self.active_category:
            self.visible_nodes = self.categories.get(self.active_category, [])
        else:
            self.visible_nodes = []
        content_height = len(self.visible_nodes) * (self.node_height + self.node_padding)
        available_height = self.rect.height - self.tab_height - 2 * self.CONTENT_TOP_PADDING
        self.max_scroll = max(0, content_height - available_height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)
        return
    
    def _draw_tabs(self, surface) -> None:
        """
        Draw all category tabs
        
        Args:
            surface: Pygame surface to draw on
        """
        for category, tab_rect in self.tab_rects.items():
            if category == self.active_category:
                color = self.tab_active_color
            elif category == self.hovered_tab:
                color = self.tab_hover_color
            else:
                color = self.tab_color
            draw.rect(surface, color, tab_rect)
            draw.rect(surface, self.TAB_BORDER_COLOR, tab_rect, self.TAB_BORDER_WIDTH)
            text = self.font.render(category, True, self.text_color)
            text_rect = text.get_rect(center=tab_rect.center)
            surface.blit(text, text_rect)
        return
    
    def _draw_nodes(self, surface, content_rect: Rect) -> None:
        """
        Draw all visible nodes with clipping
        
        Args:
            surface: Pygame surface to draw on
            content_rect: Rectangle defining the content area
        """
        clip_rect = surface.get_clip()
        surface.set_clip(content_rect)
        visible_items = self._get_visible_node_rects(content_rect)
        for node, node_rect in visible_items:
            self._draw_node(surface, node, node_rect)
        surface.set_clip(clip_rect)
        return
    
    def _draw_node(self, surface, node: NodeTemplate, rect: Rect) -> None:
        """
        Draw a single node
        
        Args:
            surface: Pygame surface to draw on
            node: Node template to draw
            rect: Rectangle to draw the node in
        """
        color = self.node_hover_color if node == self.hovered_node else node.color
        draw.rect(surface, color, rect, border_radius=self.NODE_BORDER_RADIUS)
        draw.rect(surface, self.NODE_BORDER_COLOR, rect, self.NODE_BORDER_WIDTH, 
                 border_radius=self.NODE_BORDER_RADIUS)
        name_text = self.font.render(node.name, True, self.text_color)
        name_rect = name_text.get_rect(
            centerx=rect.centerx,
            top=rect.y + self.NAME_TEXT_OFFSET
        )
        surface.blit(name_text, name_rect)
        if node.description:
            desc_font_size = max(self.MIN_DESC_FONT_SIZE, self.font_size - self.DESC_FONT_SIZE_REDUCTION)
            desc_font = font.SysFont(None, desc_font_size)
            desc_text = desc_font.render(node.description, True, self.DESCRIPTION_TEXT_COLOR)
            desc_rect = desc_text.get_rect(
                centerx=rect.centerx,
                top=name_rect.bottom + self.DESC_TEXT_OFFSET
            )
            surface.blit(desc_text, desc_rect)
        return
    
    def _draw_scrollbar(self, surface, content_rect: Rect) -> None:
        """
        Draw scrollbar if needed
        
        Args:
            surface: Pygame surface to draw on
            content_rect: Rectangle defining the content area
        """
        scrollbar_rect = self._calculate_scrollbar_rect(content_rect)
        if scrollbar_rect:
            draw.rect(surface, self.SCROLLBAR_COLOR, scrollbar_rect, 
                     border_radius=self.SCROLLBAR_BORDER_RADIUS)
        return
    
    def _calculate_content_rect(self) -> Rect:
        """
        Calculate the content area rectangle (below tabs)
        
        Returns:
            Rectangle defining the content area
        """
        return Rect(
            self.rect.x,
            self.rect.y + self.tab_height,
            self.rect.width,
            self.rect.height - self.tab_height
        )
    
    def _get_visible_node_rects(self, content_rect: Rect) -> List[Tuple[NodeTemplate, Rect]]:
        """
        Get only nodes that are visible in viewport (culling optimization)
        
        Args:
            content_rect: Rectangle defining the content area
            
        Returns:
            List of tuples (node, rect) for visible nodes only
        """
        visible = []
        y_offset = content_rect.y + self.CONTENT_TOP_PADDING - self.scroll_offset
        for node in self.visible_nodes:
            node_rect = Rect(
                self.rect.x + self.node_padding,
                y_offset,
                self.rect.width - 2 * self.node_padding,
                self.node_height
            )
            if not (node_rect.bottom < content_rect.y or node_rect.top > content_rect.bottom):
                visible.append((node, node_rect))
            y_offset += self.node_height + self.node_padding
        return visible
    
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
        total_height = len(self.visible_nodes) * (self.node_height + self.node_padding)
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