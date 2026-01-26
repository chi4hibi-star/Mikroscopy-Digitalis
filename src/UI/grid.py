from pygame import draw
from UI.base_ui import BaseUI


class Grid(BaseUI):
    def __init__(self,
                 rel_pos=(0, 0),
                 rel_size=(0.5, 0.5),
                 rows=3,
                 cols=3,
                 line_color=None,
                 cell_padding=0.1,
                 reference_resolution=(1920, 1080)):
        """
        Initialize the Grid
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            rows: Number of rows in the grid
            cols: Number of columns in the grid
            line_color: RGB color for grid lines (None for no lines)
            cell_padding: Padding as fraction of cell size (0.1 = 10% padding)
            reference_resolution: Reference resolution for scaling
        """
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.rows = rows
        self.cols = cols
        self.line_color = line_color
        self.cell_padding = cell_padding
        self.cell_width = self.rect.width / self.cols
        self.cell_height = self.rect.height / self.rows
        self.objects = [[None for _ in range(cols)] for _ in range(rows)]
        return
    
    def update_layout(self, window_size):
        """Update grid size and position, and resize all child elements"""
        if not self.should_update_layout(window_size):
            return
        self.calculate_absolute_rect(window_size)
        self.cell_width = self.rect.width / self.cols
        self.cell_height = self.rect.height / self.rows
        for r in range(self.rows):
            for c in range(self.cols):
                obj = self.objects[r][c]
                if obj:
                    self._update_object_for_grid(obj, r, c)
        return
    
    def handle_events(self, events):
        """
        Handle pygame events and pass them to child objects
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_event(events)
        for row in self.objects:
            for obj in row:
                if obj:
                    obj.handle_events(events)
        return
    
    def update(self):
        """
        Update all child objects (called every frame)
        """
        for row in self.objects:
            for obj in row:
                if obj:
                    obj.update()
        return
    
    def draw(self, surface):
        """
        Draw the grid and all child objects
        
        Args:
            surface: Pygame surface to draw on
        """
        if self.line_color:
            for c in range(self.cols + 1):
                x = self.rect.left + c * self.cell_width
                draw.line(surface, self.line_color, (x, self.rect.top), (x, self.rect.bottom))
            for r in range(self.rows + 1):
                y = self.rect.top + r * self.cell_height
                draw.line(surface, self.line_color, (self.rect.left, y), (self.rect.right, y))
        for r in range(self.rows):
            for c in range(self.cols):
                obj = self.objects[r][c]
                if obj:
                    obj.draw(surface)
        return
    
    def _update_object_for_grid(self, obj, row, col):
        """Update object's relative positioning to work within grid cell"""
        cell_width = self.rect.width / self.cols
        cell_height = self.rect.height / self.rows
        obj_width = cell_width * (1 - self.cell_padding)
        obj_height = cell_height * (1 - self.cell_padding)
        obj._grid_managed = True
        obj.rect.width = int(obj_width)
        obj.rect.height = int(obj_height)
        self._position_object(obj, row, col, obj._grid_align, obj._grid_rel_pos)
        if hasattr(obj, 'update_layout') and self.current_window_size:
            obj.update_layout(self.current_window_size)
        return
    
    def _position_object(self, obj, row, col, align=None, rel_pos=None):
        """
        Position an object within its grid cell
        
        Args:
            obj: The UI object to position
            row: Row index
            col: Column index
            align: Alignment string ("center", "left", "right", "bottom", or None)
            rel_pos: Relative position tuple (x, y) within cell, or None
        """
        cell_x = self.rect.left + col * self.cell_width
        cell_y = self.rect.top + row * self.cell_height
        if rel_pos is not None:
            x = cell_x + rel_pos[0] * (self.cell_width - obj.rect.width)
            y = cell_y + rel_pos[1] * (self.cell_height - obj.rect.height)
        elif align == "center":
            x = cell_x + (self.cell_width - obj.rect.width) / 2
            y = cell_y + (self.cell_height - obj.rect.height) / 2
        elif align == "left":
            x = cell_x
            y = cell_y + (self.cell_height - obj.rect.height) / 2
        elif align == "right":
            x = cell_x + self.cell_width - obj.rect.width
            y = cell_y + (self.cell_height - obj.rect.height) / 2
        elif align == "bottom":
            x = cell_x + (self.cell_width - obj.rect.width) / 2
            y = cell_y + self.cell_height - obj.rect.height
        elif align == "top":
            x = cell_x + (self.cell_width - obj.rect.width) / 2
            y = cell_y
        else:
            x, y = cell_x, cell_y
        obj.rect.topleft = (x, y)
        return
    
    def add_object(self, obj, row, col, align=None, rel_pos=None):
        """Add an object to a grid cell"""
        if row < self.rows and col < self.cols:
            self.objects[row][col] = obj
            obj._grid_align = align
            obj._grid_rel_pos = rel_pos
            self._update_object_for_grid(obj, row, col)
            return True
        return False
    
    def remove_object(self, row, col):
        """
        Remove an object from a grid cell
        
        Args:
            row: Row index
            col: Column index
        
        Returns:
            The removed object, or None if cell was empty
        """
        if row < self.rows and col < self.cols:
            obj = self.objects[row][col]
            self.objects[row][col] = None
            return obj
        return None
    
    def get_object(self, row, col):
        """
        Get the object at a grid cell
        
        Args:
            row: Row index
            col: Column index
        
        Returns:
            The object at that cell, or None
        """
        if row < self.rows and col < self.cols:
            return self.objects[row][col]
        return None