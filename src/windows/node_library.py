from pygame import Rect, draw, font, mouse, MOUSEBUTTONDOWN, MOUSEWHEEL, MOUSEMOTION
from windows.base_window import BaseWindow

class NodeTemplate:
    def __init__(self, name, category, description="", color=(100, 150, 200)):
        self.name = name
        self.category = category
        self.description = description
        self.color = color
        self.rect = Rect(0, 0, 0, 0)
        self.hovered = False
        
class TabbedNodeViewer(BaseWindow):
    def __init__(self,
                 rel_pos=(0.001, 0.051),
                 rel_size=(0.248, 0.948),
                 reference_resolution=(1920, 1080),
                 background_color=(40, 40, 40),
                 tab_color=(60, 60, 60),
                 tab_active_color=(80, 80, 80),
                 tab_hover_color=(70, 70, 70),
                 node_color=(100, 150, 200),
                 node_hover_color=(120, 170, 220),
                 text_color=(255, 255, 255)):
        super().__init__(rel_pos, rel_size, reference_resolution, background_color)
        self.tab_color = tab_color
        self.tab_active_color = tab_active_color
        self.tab_hover_color = tab_hover_color
        self.node_color = node_color
        self.node_hover_color = node_hover_color
        self.text_color = text_color
        self.base_tab_height = 40
        self.tab_height = 40
        self.base_node_height = 60
        self.node_height = 60
        self.base_node_padding = 10
        self.node_padding = 10
        self.categories = {}
        self.active_category = None
        self.tab_rects = {}
        self.hovered_tab = None
        self.nodes = []
        self.visible_nodes = []
        self.hovered_node = None
        self.dragging_node = None
        self.drag_offset = (0, 0)
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 30
        return
    
    def update_layout(self, window_size):
        """Update tabbed node viewer size and position based on window size"""
        super().update_layout(window_size)
        scale_factor = self.get_scale_factor()
        self.tab_height = max(30, int(self.base_tab_height * scale_factor))
        self.node_height = max(50, int(self.base_node_height * scale_factor))
        self.node_padding = max(5, int(self.base_node_padding * scale_factor))
        self._update_tab_rects()
        self._update_visible_nodes()
        return
    
    def handle_events(self, events):
        self.handle_resize_events(events)
        for event in events:
            if event.type == MOUSEWHEEL:
                if self.rect.collidepoint(mouse.get_pos()):
                    self.scroll_offset -= event.y * self.scroll_speed
                    self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    for category, tab_rect in self.tab_rects.items():
                        if tab_rect.collidepoint(event.pos):
                            self.active_category = category
                            self._update_visible_nodes()
                            break
                    content_rect = Rect(
                        self.rect.x,
                        self.rect.y + self.tab_height,
                        self.rect.width,
                        self.rect.height - self.tab_height
                    )
                    if content_rect.collidepoint(event.pos):
                        y_offset = self.rect.y + self.tab_height + 10 - self.scroll_offset
                        for node in self.visible_nodes:
                            node_rect = Rect(
                                self.rect.x + self.node_padding,
                                y_offset,
                                self.rect.width - 2 * self.node_padding,
                                self.node_height
                            )
                            if node_rect.collidepoint(event.pos):
                                self.dragging_node = node
                                self.drag_offset = (
                                    event.pos[0] - node_rect.x,
                                    event.pos[1] - node_rect.y
                                )
                                break
                            y_offset += self.node_height + self.node_padding
            elif event.type == MOUSEMOTION:
                if self.dragging_node:
                    pass
        return
    
    def update(self):
        mouse_pos = mouse.get_pos()
        self.hovered_tab = None
        for category, tab_rect in self.tab_rects.items():
            if tab_rect.collidepoint(mouse_pos):
                self.hovered_tab = category
                break
        self.hovered_node = None
        content_rect = Rect(
            self.rect.x,
            self.rect.y + self.tab_height,
            self.rect.width,
            self.rect.height - self.tab_height
        )
        if content_rect.collidepoint(mouse_pos) and not self.dragging_node:
            y_offset = self.rect.y + self.tab_height + 10 - self.scroll_offset
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
    
    def draw(self, surface):
        draw.rect(surface, self.background_color, self.rect)
        draw.rect(surface, (100, 100, 100), self.rect, 2)
        for category, tab_rect in self.tab_rects.items():
            if category == self.active_category:
                color = self.tab_active_color
            elif category == self.hovered_tab:
                color = self.tab_hover_color
            else:
                color = self.tab_color
            draw.rect(surface, color, tab_rect)
            draw.rect(surface, (80, 80, 80), tab_rect, 1)
            text = self.font.render(category, True, self.text_color)
            text_rect = text.get_rect(center=tab_rect.center)
            surface.blit(text, text_rect)
        content_rect = Rect(
            self.rect.x,
            self.rect.y + self.tab_height,
            self.rect.width,
            self.rect.height - self.tab_height
        )
        clip_rect = surface.get_clip()
        surface.set_clip(content_rect)
        y_offset = content_rect.y + 10 - self.scroll_offset
        for node in self.visible_nodes:
            node_rect = Rect(
                self.rect.x + self.node_padding,
                y_offset,
                self.rect.width - 2 * self.node_padding,
                self.node_height
            )
            if node_rect.bottom < content_rect.y or node_rect.top > content_rect.bottom:
                y_offset += self.node_height + self.node_padding
                continue
            if node == self.hovered_node:
                color = self.node_hover_color
            else:
                color = node.color
            draw.rect(surface, color, node_rect, border_radius=5)
            draw.rect(surface, (150, 150, 150), node_rect, 2, border_radius=5)
            name_text = self.font.render(node.name, True, self.text_color)
            name_rect = name_text.get_rect(
                centerx=node_rect.centerx,
                top=node_rect.y + 8
            )
            surface.blit(name_text, name_rect)
            if node.description:
                desc_font = font.SysFont(None, max(12, self.font_size - 4))
                desc_text = desc_font.render(node.description, True, (200, 200, 200))
                desc_rect = desc_text.get_rect(
                    centerx=node_rect.centerx,
                    top=name_rect.bottom + 4
                )
                surface.blit(desc_text, desc_rect)
            y_offset += self.node_height + self.node_padding
        surface.set_clip(clip_rect)
        if self.max_scroll > 0:
            scrollbar_height = max(20, int(content_rect.height * 
                                         (content_rect.height / (len(self.visible_nodes) * 
                                         (self.node_height + self.node_padding)))))
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
    
    def add_category(self, category_name):
        if category_name not in self.categories:
            self.categories[category_name] = []
            if self.active_category is None:
                self.active_category = category_name
        return
    
    def add_node(self, name, category, description="", color=None):
        if category not in self.categories:
            self.add_category(category)
        node_color = color if color else self.node_color
        node = NodeTemplate(name, category, description, node_color)
        self.categories[category].append(node)
        self.nodes.append(node)
        self._update_visible_nodes()
        return
    
    def _update_visible_nodes(self):
        if self.active_category:
            self.visible_nodes = self.categories.get(self.active_category, [])
        else:
            self.visible_nodes = []
        content_height = len(self.visible_nodes) * (self.node_height + self.node_padding)
        available_height = self.rect.height - self.tab_height - 20
        self.max_scroll = max(0, content_height - available_height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)
        return
    
    def _update_tab_rects(self):
        self.tab_rects = {}
        if not self.categories:
            return
        num_tabs = len(self.categories)
        tab_width = self.rect.width / num_tabs
        for i, category in enumerate(self.categories.keys()):
            tab_x = self.rect.x + i * tab_width
            tab_rect = Rect(tab_x, self.rect.y, tab_width, self.tab_height)
            self.tab_rects[category] = tab_rect
        return
    
    def get_dragging_node(self):
        if self.dragging_node:
            mouse_pos = mouse.get_pos()
            return self.dragging_node, mouse_pos
        return None, None
    
    def stop_dragging(self):
        self.dragging_node = None
        return