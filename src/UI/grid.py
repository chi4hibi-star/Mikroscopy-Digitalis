from pygame import draw
from UI.base_ui import BaseUI
from typing import Callable, Optional, Tuple, Any, List

class Grid(BaseUI):
    def __init__(self,
                 rel_pos: Tuple[float, float] = (0, 0),
                 rel_size: Tuple[float, float] = (0.5, 0.5),
                 rows: int = 3,
                 cols: int = 3,
                 line_color: Optional[Tuple[int, int, int]] = None,
                 cell_padding: float = 0.1,
                 reference_resolution: Tuple[int, int] = (1920, 1080)) -> None:
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
        self.cell_width = 0
        self.cell_height = 0
        self.objects:List[List[Optional[Any]]] = [[None for _ in range(cols)] for _ in range(rows)]
        return
    
    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update grid size and position, and resize all child elements
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
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
    
    def handle_events(self, events: list) -> None:
        """
        Handle pygame events and pass them to child objects
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_event(events)
        self._iterate_every_object(lambda obj: obj.handle_events(events))
        return
    
    def update(self):
        """
        Update all child objects (called every frame)
        """
        self._iterate_every_object(lambda obj: obj.update())
        return
    
    def draw(self, surface) -> None:
        """
        Draw the grid and all child objects
        
        Args:
            surface: Pygame surface to draw on
        """
        if self.line_color:
            self._draw_grid_lines(surface)
        self._iterate_every_object(lambda obj: obj.draw(surface))
        return
    
    def _iterate_every_object(self, func: Callable[[Any], None]) -> None:
        """
        Apply a function to every object in the grid
        
        Args:
            surface: Pygame surface (passed to function)
            func: Function that takes (obj, surface) as arguments
        """
        for row in self.objects:
            for obj in row:
                if obj:
                    func(obj)
        return
    
    def _draw_grid_lines(self, surface) -> None:
        """
        Draw the grid lines
        
        Args:
            surface: Pygame surface to draw on
        """
        for c in range(self.cols + 1):
            x = self.rect.left + c * self.cell_width
            draw.line(surface, self.line_color, (x, self.rect.top), (x, self.rect.bottom))
        for r in range(self.rows + 1):
            y = self.rect.top + r * self.cell_height
            draw.line(surface, self.line_color, (self.rect.left, y), (self.rect.right, y))
        return
    
    def _update_object_for_grid(self, obj:Any, row:int, col:int)->None:
        """
        Update object's relative positioning to work within grid cell
        
        Args:
            obj: The UI object to update
            row: Row index
            col: Column index
        """
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
    
    def _position_object(self, obj: Any, row: int, col: int, 
                        align: Optional[str] = None, 
                        rel_pos: Optional[Tuple[float, float]] = None) -> None:
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
    
    def add_object(self, obj: Any, row: int, col: int, 
                   align: Optional[str] = None, 
                   rel_pos: Optional[Tuple[float, float]] = None) -> bool:
        """
        Add an object to a grid cell
        
        Args:
            obj: The UI object to add
            row: Row index (0 to rows-1)
            col: Column index (0 to cols-1)
            align: Alignment string ("center", "left", "right", "top", "bottom")
            rel_pos: Relative position tuple (x, y) within cell (0.0 to 1.0)
        
        Returns:
            True if object was added successfully, False if out of bounds
        """
        if not self._is_valid_position(row,col):
            return False
        self.objects[row][col] = obj
        obj._grid_align = align
        obj._grid_rel_pos = rel_pos
        self._update_object_for_grid(obj, row, col)
        return True
    
    def _is_valid_position(self, row: int, col: int) -> bool:
        """
        Check if a grid position is valid
        
        Args:
            row: Row index
            col: Column index
        
        Returns:
            True if position is within grid bounds
        """
        return 0 <= row < self.rows and 0 <= col < self.cols
    
    def remove_object(self, row: int, col: int) -> Optional[Any]:
        """
        Remove an object from a grid cell
        
        Args:
            row: Row index
            col: Column index
        
        Returns:
            The removed object, or None if cell was empty or out of bounds
        """
        if not self._is_valid_position(row, col):
            return None
        obj = self.objects[row][col]
        self.objects[row][col] = None
        return obj
    
    def get_object(self, row: int, col: int) -> Optional[Any]:
        """
        Get the object at a grid cell
        
        Args:
            row: Row index
            col: Column index
        
        Returns:
            The object at that cell, or None if empty or out of bounds
        """
        if not self._is_valid_position(row, col):
            return None
        return self.objects[row][col]
    
    def clear(self) -> None:
        """
        Remove all objects from the grid
        """
        self.objects = [[None for _ in range(self.cols)] for _ in range(self.rows)]
        return
    
    def get_all_objects(self) -> List[Any]:
        """
        Get a flat list of all objects in the grid (excluding None)
        
        Returns:
            List of all objects
        """
        objects = []
        for row in self.objects:
            for obj in row:
                if obj is not None:
                    objects.append(obj)
        return objects
    
    def resize_grid(self, new_rows: int, new_cols: int) -> None:
        """
        Resize the grid (warning: clears all objects)
        
        Args:
            new_rows: New number of rows
            new_cols: New number of columns
        """
        self.rows = new_rows
        self.cols = new_cols
        self.objects = [[None for _ in range(new_cols)] for _ in range(new_rows)]
        if self.current_window_size:
            self.update_layout(self.current_window_size)
        return