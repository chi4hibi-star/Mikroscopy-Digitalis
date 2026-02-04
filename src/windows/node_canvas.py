from pygame import Rect, draw, font, mouse, MOUSEWHEEL, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, K_DELETE, KEYDOWN
from uuid import uuid4
from windows.base_window import BaseWindow
from typing import Tuple, List, Optional, Dict, Any
from enum import Enum

class NodeType(Enum):
    """Enumeration of node types"""
    INPUT = "input"
    OUTPUT = "output"
    PROCESS = "process"
    ALGORITHM = "algorithm"


class ConnectionPoint:
    """
    Represents a connection point on a node
    
    Attributes:
        name: Name of this connection point (e.g., "image", "data", "kernel_size")
        position: (x, y) position in canvas coordinates
        is_input: True if this is an input point, False for output
    """
    def __init__(self, name: str, position: Tuple[float, float], is_input: bool = True):
        self.name = name
        self.position = position
        self.is_input = is_input
        return
    
    def is_near(self, pos: Tuple[float, float], threshold: float = 15.0) -> bool:
        """
        Check if a position is near this connection point
        
        Args:
            pos: Position to check (x, y)
            threshold: Distance threshold in pixels
            
        Returns:
            True if position is within threshold distance
        """
        dx = pos[0] - self.position[0]
        dy = pos[1] - self.position[1]
        return (dx * dx + dy * dy) < threshold * threshold


class CanvasNode:
    """
    Represents a node instance on the canvas
    
    A node can be an input source, output destination, processing step,
    or an algorithm (encapsulated pipeline).
    """
    
    # Visual constants
    BASE_WIDTH = 150
    BASE_HEIGHT = 80
    HEADER_HEIGHT = 30
    PARAM_SPACING = 20
    OUTPUT_SPACING = 20
    CONNECTION_POINT_THRESHOLD = 15
    
    # Colors
    HEADER_DARKEN_AMOUNT = 30
    
    def __init__(self, 
                 name: str, 
                 category: str, 
                 x: float, 
                 y: float, 
                 color: Tuple[int, int, int] = (100, 150, 200), 
                 parameters: Optional[Dict[str, Any]] = None, 
                 parameter_info: Optional[List[Dict[str, Any]]] = None, 
                 node_type: str = "process"):
        """
        Initialize a canvas node
        
        Args:
            name: Display name of the node
            category: Category this node belongs to
            x: X position on canvas
            y: Y position on canvas
            color: RGB color for visual identification
            parameters: Dictionary of parameter values
            parameter_info: List of parameter definitions
            node_type: Type of node ("input", "output", "process", "algorithm")
        """
        self.id = str(uuid4())
        self.name = name
        self.category = category
        self.color = color
        self.parameters = parameters or {}
        self.parameter_info = parameter_info or []
        self.node_type = NodeType(node_type)
        self.rect = self._calculate_rect(x, y)
        self.header_height = self.HEADER_HEIGHT
        self.input_points: Dict[str, ConnectionPoint] = {}
        self.output_points: Dict[str, ConnectionPoint] = {}
        self._update_connection_points()
        self.selected = False
        self.dragging = False
        self.drag_offset = (0.0, 0.0)
        if self.node_type == NodeType.ALGORITHM:
            self.pipeline_data: Optional[Dict[str, Any]] = None
            self.algorithm_outputs: List[str] = ["image"]
        return
    
    def _calculate_rect(self, x: float, y: float) -> Rect:
        """
        Calculate node rectangle based on type and parameters
        
        Args:
            x: X position
            y: Y position
            
        Returns:
            Pygame Rect for the node
        """
        connectable_params = [p for p in self.parameter_info if p.get('connectable', False)]
        if self.node_type == NodeType.OUTPUT:
            total_height = self.BASE_HEIGHT + self.PARAM_SPACING
        elif self.node_type == NodeType.INPUT:
            total_height = self.BASE_HEIGHT
        elif self.node_type == NodeType.ALGORITHM:
            total_height = self.BASE_HEIGHT + len(connectable_params) * self.PARAM_SPACING
        else:
            total_height = self.BASE_HEIGHT + len(connectable_params) * self.PARAM_SPACING
        return Rect(x, y, self.BASE_WIDTH, total_height)
    
    def _update_connection_points(self) -> None:
        """Update all connection point positions based on node type"""
        self.input_points.clear()
        self.output_points.clear()
        if self.node_type == NodeType.INPUT:
            self._setup_input_node_connections()
        elif self.node_type == NodeType.OUTPUT:
            self._setup_output_node_connections()
        elif self.node_type == NodeType.ALGORITHM:
            self._setup_algorithm_node_connections()
        else:
            self._setup_process_node_connections()
        return
    
    def _setup_input_node_connections(self) -> None:
        """Setup connection points for input node"""
        output_pos = (self.rect.right, self.rect.centery)
        self.output_points["image"] = ConnectionPoint("image", output_pos, is_input=False)
        return
    
    def _setup_output_node_connections(self) -> None:
        """Setup connection points for output node"""
        y_offset = self.rect.top + self.header_height + 10
        self.input_points["image"] = ConnectionPoint("image", (self.rect.left, y_offset), is_input=True)
        y_offset += 40
        self.input_points["data"] = ConnectionPoint("data", (self.rect.left, y_offset), is_input=True)
        return
    
    def _setup_algorithm_node_connections(self) -> None:
        """Setup connection points for algorithm node"""
        y_offset = self.rect.top + self.header_height + 10
        self.input_points["image"] = ConnectionPoint("image", (self.rect.left, y_offset), is_input=True)
        y_offset += 30
        connectable_params = [p for p in self.parameter_info if p.get('connectable', False)]
        for param in connectable_params:
            param_name = param['name']
            self.input_points[param_name] = ConnectionPoint(param_name, (self.rect.left, y_offset), is_input=True)
            y_offset += 25
        y_offset = self.rect.top + self.header_height + 10
        outputs = getattr(self, 'algorithm_outputs', ['image'])
        for output_name in outputs:
            self.output_points[output_name] = ConnectionPoint(output_name, (self.rect.right, y_offset), is_input=False)
            y_offset += 20
        return
    
    def _setup_process_node_connections(self) -> None:
        """Setup connection points for process node"""
        y_offset = self.rect.top + self.header_height + 10
        self.input_points["image"] = ConnectionPoint("image", (self.rect.left, y_offset), is_input=True)
        self.output_points["image"] = ConnectionPoint("image", (self.rect.right, y_offset), is_input=False)
        y_offset += 20
        if self.name == "Object Characteristics":
            self.output_points["data"] = ConnectionPoint("data", (self.rect.right, y_offset), is_input=False)
            y_offset += 20
        y_offset = self.rect.top + self.header_height + 30
        connectable_params = [p for p in self.parameter_info if p.get('connectable', False)]
        for param in connectable_params:
            param_name = param['name']
            self.input_points[param_name] = ConnectionPoint(param_name, (self.rect.left, y_offset), is_input=True)
            y_offset += 25
        return
    
    def update_connection_points(self) -> None:
        """Public method to update connection points (after move/resize)"""
        self._update_connection_points()
        return
    
    def contains_point(self, pos: Tuple[float, float]) -> bool:
        """
        Check if a point is inside this node
        
        Args:
            pos: Position to check (x, y)
            
        Returns:
            True if point is inside node
        """
        return self.rect.collidepoint(pos)
    
    def get_input_at_position(self, pos: Tuple[float, float]) -> Optional[str]:
        """
        Get input connection point name at position
        
        Args:
            pos: Position to check
            
        Returns:
            Input point name or None
        """
        for name, point in self.input_points.items():
            if point.is_near(pos, self.CONNECTION_POINT_THRESHOLD):
                return name
        return None
    
    def get_output_at_position(self, pos: Tuple[float, float]) -> Optional[str]:
        """
        Get output connection point name at position
        
        Args:
            pos: Position to check
            
        Returns:
            Output point name or None
        """
        for name, point in self.output_points.items():
            if point.is_near(pos, self.CONNECTION_POINT_THRESHOLD):
                return name
        return None
    
    def move_to(self, x: float, y: float) -> None:
        """
        Move node to a new position
        
        Args:
            x: New X position
            y: New Y position
        """
        self.rect.x = x
        self.rect.y = y
        self._update_connection_points()
        return


class Connection:
    """
    Represents a connection between two nodes
    
    Connections can be from any output point to any input point,
    allowing flexible data flow between nodes.
    """
    def __init__(self, 
                 from_node: CanvasNode, 
                 to_node: CanvasNode, 
                 to_parameter: Optional[str] = None, 
                 from_output: str = "image"):
        """
        Initialize a connection
        
        Args:
            from_node: Source node
            to_node: Destination node
            to_parameter: Name of input parameter (None for main input)
            from_output: Name of output to connect from
        """
        self.id = str(uuid4())
        self.from_node = from_node
        self.to_node = to_node
        self.to_parameter = to_parameter or "image"
        self.from_output = from_output
        self.color = (150, 150, 150)
        self.selected = False
        return
    
    def get_start_position(self) -> Optional[Tuple[float, float]]:
        """Get the start position of this connection"""
        output_point = self.from_node.output_points.get(self.from_output)
        return output_point.position if output_point else None
    
    def get_end_position(self) -> Optional[Tuple[float, float]]:
        """Get the end position of this connection"""
        input_point = self.to_node.input_points.get(self.to_parameter)
        return input_point.position if input_point else None


class NodeCanvas(BaseWindow):
    """
    Visual programming canvas for connecting nodes
    
    Features:
    - Drag-and-drop node placement
    - Visual connection system
    - Pan and zoom
    - Grid background
    - Support for algorithm nodes (embedded pipelines)
    """
    
    # Visual constants
    MIN_ZOOM = 0.3
    MAX_ZOOM = 3.0
    ZOOM_STEP = 0.1
    GRID_SIZE = 20
    MIN_GRID_SIZE_DISPLAY = 5
    
    # Node rendering
    NODE_BORDER_WIDTH_NORMAL = 2
    NODE_BORDER_WIDTH_SPECIAL = 3
    NODE_BORDER_RADIUS = 5
    NODE_SELECTION_INFLATE = 4
    NODE_SELECTION_BORDER = 3
    NODE_SELECTION_RADIUS = 8
    
    # Connection rendering
    CONNECTION_WIDTH = 3
    CONNECTION_BEZIER_SEGMENTS = 20
    CONNECTION_CONTROL_OFFSET_MIN = 50
    CONNECTION_CONTROL_OFFSET_MAX = 200
    CONNECTION_CONTROL_FACTOR = 0.5
    
    # Connection points
    CONNECTION_POINT_RADIUS = 8
    CONNECTION_POINT_BORDER = 2
    CONNECTION_POINT_LABEL_OFFSET = 5
    
    # Text rendering
    CATEGORY_TEXT_Y_OFFSET = 15
    NAME_TEXT_Y_OFFSET = 8
    DESC_TEXT_Y_OFFSET = 4
    TINY_FONT_SIZE = 12
    MIN_SCALED_FONT = 6
    MIN_SCALED_TINY_FONT = 6
    
    # Colors
    GRID_COLOR = (50, 50, 50)
    CANVAS_BORDER_COLOR = (100, 100, 100)
    NODE_BORDER_COLOR = (200, 200, 200)
    NODE_TEXT_COLOR = (0, 0, 0)
    CONNECTION_TEMP_COLOR = (200, 200, 100)
    CONNECTION_POINT_BORDER_COLOR = (50, 50, 50)
    INPUT_POINT_COLOR = (100, 200, 100)
    OUTPUT_POINT_COLOR = (200, 100, 100)
    PARAM_INPUT_POINT_COLOR = (100, 150, 200)
    
    # Input node defaults
    INPUT_NODE_POS = (50, 100)
    INPUT_NODE_COLOR = (50, 180, 100)
    OUTPUT_NODE_POS = (500, 100)
    OUTPUT_NODE_COLOR = (180, 50, 50)
    OUTPUT_NODE_HEIGHT = 100
    
    def __init__(self,
                 rel_pos: Tuple[float, float] = (0.251, 0.051),
                 rel_size: Tuple[float, float] = (0.498, 0.608),
                 reference_resolution: Tuple[int, int] = (1920, 1080),
                 background_color: Tuple[int, int, int] = (30, 30, 30),
                 grid_color: Tuple[int, int, int] = (50, 50, 50),
                 text_color: Tuple[int, int, int] = (0, 0, 0),
                 selection_color: Tuple[int, int, int] = (255, 200, 0),
                 connection_color: Tuple[int, int, int] = (150, 150, 150),
                 node_definitions: Optional[Dict[str, Any]] = None):
        """
        Initialize the NodeCanvas
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
            background_color: RGB color for canvas background
            grid_color: RGB color for grid lines
            text_color: RGB color for text on nodes
            selection_color: RGB color for selection highlight
            connection_color: RGB color for connections
            node_definitions: Dictionary of node type definitions
        """
        super().__init__(rel_pos, rel_size, reference_resolution, background_color)
        self.grid_color = grid_color
        self.text_color = text_color
        self.selection_color = selection_color
        self.connection_color = connection_color
        self.node_label_color = self.NODE_TEXT_COLOR
        self.base_font_size = 20
        self.base_small_font_size = 16
        self.small_font: Optional[font.Font] = None
        self.node_definitions = node_definitions or {"categories": []}
        self.nodes: List[CanvasNode] = []
        self.connections: List[Connection] = []
        self.selected_nodes: List[CanvasNode] = []
        self.dragging_node: Optional[CanvasNode] = None
        self.dragging_connection: Optional[CanvasNode] = None
        self.dragging_output_name: str = "output"
        self.temp_connection_pos: Optional[Tuple[int, int]] = None
        self.pan_offset = [0.0, 0.0]
        self.is_panning = False
        self.pan_start: Optional[Tuple[int, int]] = None
        self.zoom = 1.0
        self.grid_size = self.GRID_SIZE
        self.show_grid = True
        self._add_default_nodes()
        return
    
    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update canvas size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        super().update_layout(window_size)
        scale_factor = self.get_scale_factor()
        self.small_font_size = max(14, int(16 * scale_factor))
        self.small_font = font.SysFont(None, self.small_font_size)
        return
    
    def handle_events(self, events: list) -> None:
        """
        Handle user input events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_events(events)
        for event in events:
            if event.type == MOUSEWHEEL:
                if self.rect.collidepoint(mouse.get_pos()):
                    self._handle_zoom(event)
            elif event.type == MOUSEBUTTONDOWN:
                if not self.rect.collidepoint(event.pos):
                    continue
                self._handle_mouse_down(event)
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self._handle_left_mouse_up(event)
                    self.is_panning = False
                    self.pan_start = None
                elif event.button == 3:
                    self._handle_right_mouse_up(event)
            elif event.type == MOUSEMOTION:
                self._handle_mouse_motion(event)
            elif event.type == KEYDOWN:
                if event.key == K_DELETE:
                    self._delete_selected_nodes()
        return
    
    def update(self) -> None:
        """Update canvas state (called every frame)"""
        pass
    
    def draw(self, surface) -> None:
        """
        Draw the canvas and all its contents
        
        Args:
            surface: Pygame surface to draw on
        """
        draw.rect(surface, self.background_color, self.rect)
        clip_rect = surface.get_clip()
        surface.set_clip(self.rect)
        if self.show_grid:
            self._draw_grid(surface)
        for connection in self.connections:
            self._draw_connection(surface, connection)
        if self.dragging_connection and self.temp_connection_pos:
            self._draw_temp_connection(surface)
        for node in self.nodes:
            self._draw_node(surface, node)
        draw.rect(surface, self.CANVAS_BORDER_COLOR, self.rect, 2)
        surface.set_clip(clip_rect)
        return
    
    def add_node_from_template(self, template: Any, screen_pos: Tuple[int, int]) -> Optional[CanvasNode]:
        """
        Add a node to the canvas from a template at screen position
        
        Args:
            template: Node template with name, category, color
            screen_pos: Screen position where node should appear
            
        Returns:
            Created CanvasNode or None if failed
        """
        canvas_pos = self.screen_to_canvas(screen_pos)
        param_info = self._get_parameter_info(template.name)
        parameters = {}
        for param in param_info:
            parameters[param['name']] = param['value']
        new_node = CanvasNode(
            template.name,
            template.category,
            canvas_pos[0] - 75,
            canvas_pos[1] - 40,
            template.color,
            parameters,
            param_info,
            node_type="process"
        )
        self.nodes.append(new_node)
        print(f"Added node '{template.name}' to canvas at {canvas_pos}")
        return new_node
    
    def add_algorithm_node(self, 
                          algorithm_name: str, 
                          algorithm_data: Dict[str, Any], 
                          screen_pos: Tuple[int, int], 
                          color: Tuple[int, int, int] = (150, 100, 200)) -> Optional[CanvasNode]:
        """
        Add a single algorithm node that encapsulates a pipeline
        
        Args:
            algorithm_name: Name of the algorithm
            algorithm_data: Dictionary containing pipeline data
            screen_pos: Screen position where node should appear
            color: RGB color for the node
            
        Returns:
            Created CanvasNode or None if failed
        """
        canvas_pos = self.screen_to_canvas(screen_pos)
        pipeline_data = algorithm_data.get('pipeline_data', {})
        input_params = self._extract_algorithm_inputs(pipeline_data)
        output_params = self._extract_algorithm_outputs(pipeline_data)
        new_node = CanvasNode(
            algorithm_name,
            "Algorithm",
            canvas_pos[0] - 75,
            canvas_pos[1] - 40,
            color,
            {},
            input_params,
            node_type="algorithm"
        )
        new_node.pipeline_data = pipeline_data
        new_node.algorithm_outputs = output_params
        new_node.update_connection_points()
        self.nodes.append(new_node)
        print(f"Added algorithm node '{algorithm_name}' to canvas")
        return new_node
    
    def add_connection(self, 
                      from_node: CanvasNode, 
                      to_node: CanvasNode, 
                      to_parameter: Optional[str] = None, 
                      from_output: str = "image") -> Optional[Connection]:
        """
        Add a connection between two nodes
        
        Args:
            from_node: Source node
            to_node: Destination node
            to_parameter: Input parameter name (None for main input)
            from_output: Output name to connect from
            
        Returns:
            Created Connection or None if invalid
        """
        for conn in self.connections:
            if (conn.from_node == from_node and 
                conn.to_node == to_node and 
                conn.to_parameter == to_parameter and 
                conn.from_output == from_output):
                print("Connection already exists")
                return None
        if from_node == to_node:
            print("Cannot connect node to itself")
            return None
        if from_output not in from_node.output_points:
            print(f"Cannot connect from {from_node.name}: output '{from_output}' not found")
            return None
        input_name = to_parameter or "image"
        if input_name not in to_node.input_points:
            print(f"Cannot connect to {to_node.name}: input '{input_name}' not found")
            return None
        connection = Connection(from_node, to_node, to_parameter, from_output)
        self.connections.append(connection)
        print(f"Connected '{from_node.name}.{from_output}' to '{to_node.name}.{input_name}'")
        return connection
    
    def remove_node(self, node: CanvasNode) -> None:
        """
        Remove a node and all its connections
        
        Args:
            node: Node to remove
        """
        if node.node_type in [NodeType.INPUT, NodeType.OUTPUT]:
            print(f"Cannot delete {node.node_type.value} node")
            return
        self.connections = [c for c in self.connections 
                          if c.from_node != node and c.to_node != node]
        if node in self.nodes:
            self.nodes.remove(node)
        if node in self.selected_nodes:
            self.selected_nodes.remove(node)
        return
    
    def remove_connection(self, connection: Connection) -> None:
        """
        Remove a connection
        
        Args:
            connection: Connection to remove
        """
        if connection in self.connections:
            self.connections.remove(connection)
        return
    
    def get_selected_node(self) -> Optional[CanvasNode]:
        """
        Get the currently selected node (for parameter editing)
        
        Returns:
            Selected process/algorithm node or None
        """
        if self.selected_nodes:
            selected = self.selected_nodes[0]
            if selected.node_type in [NodeType.PROCESS, NodeType.ALGORITHM]:
                return selected
        return None
    
    def screen_to_canvas(self, screen_pos: Tuple[int, int]) -> Tuple[float, float]:
        """
        Convert screen position to canvas position
        
        Args:
            screen_pos: Position in screen coordinates
            
        Returns:
            Position in canvas coordinates
        """
        return (
            (screen_pos[0] - self.rect.x - self.pan_offset[0]) / self.zoom,
            (screen_pos[1] - self.rect.y - self.pan_offset[1]) / self.zoom
        )
    
    def canvas_to_screen(self, canvas_pos: Tuple[float, float]) -> Tuple[float, float]:
        """
        Convert canvas position to screen position
        
        Args:
            canvas_pos: Position in canvas coordinates
            
        Returns:
            Position in screen coordinates
        """
        return (
            canvas_pos[0] * self.zoom + self.rect.x + self.pan_offset[0],
            canvas_pos[1] * self.zoom + self.rect.y + self.pan_offset[1]
        )
    
    def _handle_zoom(self, event) -> None:
        """Handle mouse wheel zoom"""
        mouse_pos = mouse.get_pos()
        old_canvas_pos = self.screen_to_canvas(mouse_pos)
        if event.y > 0:
            self.zoom = min(self.MAX_ZOOM, self.zoom + self.ZOOM_STEP)
        else:
            self.zoom = max(self.MIN_ZOOM, self.zoom - self.ZOOM_STEP)
        new_canvas_pos = self.screen_to_canvas(mouse_pos)
        self.pan_offset[0] += (new_canvas_pos[0] - old_canvas_pos[0]) * self.zoom
        self.pan_offset[1] += (new_canvas_pos[1] - old_canvas_pos[1]) * self.zoom
        return
    
    def _handle_mouse_down(self, event) -> None:
        """Handle mouse button down events"""
        canvas_pos = self.screen_to_canvas(event.pos)
        if event.button == 1:
            if self._try_start_connection(canvas_pos, event.pos):
                return
            if self._try_select_node(canvas_pos):
                return
            self.is_panning = True
            self.pan_start = event.pos
            for node in self.nodes:
                node.selected = False
            self.selected_nodes = []
        return
    
    def _try_start_connection(self, canvas_pos: Tuple[float, float], 
                            screen_pos: Tuple[int, int]) -> bool:
        """
        Try to start a connection from an output point
        
        Args:
            canvas_pos: Position in canvas coordinates
            screen_pos: Position in screen coordinates
            
        Returns:
            True if connection started
        """
        for node in self.nodes:
            output_name = node.get_output_at_position(canvas_pos)
            if output_name:
                self.dragging_connection = node
                self.dragging_output_name = output_name
                self.temp_connection_pos = screen_pos
                return True
        return False
    
    def _try_select_node(self, canvas_pos: Tuple[float, float]) -> bool:
        """
        Try to select and start dragging a node
        
        Args:
            canvas_pos: Position in canvas coordinates
            
        Returns:
            True if node was selected
        """
        clicked_node = self._get_node_at_position(canvas_pos)
        if clicked_node:
            clicked_node.dragging = True
            clicked_node.drag_offset = (
                canvas_pos[0] - clicked_node.rect.x,
                canvas_pos[1] - clicked_node.rect.y
            )
            if clicked_node not in self.selected_nodes:
                for node in self.nodes:
                    node.selected = False
                self.selected_nodes = [clicked_node]
                clicked_node.selected = True
            return True
        return False
    
    def _handle_left_mouse_up(self, event) -> None:
        """Handle left mouse button release"""
        for node in self.nodes:
            node.dragging = False
        if self.dragging_connection:
            self._complete_connection(event.pos)
            self.dragging_connection = None
            self.dragging_output_name = "output"
            self.temp_connection_pos = None
        return
    
    def _complete_connection(self, screen_pos: Tuple[int, int]) -> None:
        """
        Complete a connection being dragged
        
        Args:
            screen_pos: Where the connection was released
        """
        canvas_pos = self.screen_to_canvas(screen_pos)
        from_output = self.dragging_output_name
        for node in self.nodes:
            if node == self.dragging_connection:
                continue
            input_name = node.get_input_at_position(canvas_pos)
            if input_name:
                self.add_connection(self.dragging_connection, node, input_name, from_output)
                break
        return
    
    def _handle_right_mouse_up(self, event) -> None:
        """Handle right mouse button release (delete connections/nodes)"""
        canvas_pos = self.screen_to_canvas(event.pos)
        clicked_node = self._get_node_at_position(canvas_pos)
        if clicked_node:
            self._handle_node_right_click(clicked_node, canvas_pos)
        return
    
    def _handle_node_right_click(self, node: CanvasNode, canvas_pos: Tuple[float, float]) -> None:
        """
        Handle right click on a node (delete connections)
        
        Args:
            node: Node that was clicked
            canvas_pos: Position in canvas coordinates
        """
        node_left = node.rect.x
        node_width = node.rect.width
        click_x = canvas_pos[0]
        relative_x = click_x - node_left
        third = relative_x / node_width
        if third < 0.33:
            connections_to_remove = [c for c in self.connections if c.to_node == node]
            for conn in connections_to_remove:
                self.remove_connection(conn)
                print(f"Deleted connection TO '{node.name}'")
        elif third > 0.67:
            connections_to_remove = [c for c in self.connections if c.from_node == node]
            for conn in connections_to_remove:
                self.remove_connection(conn)
                print(f"Deleted connection FROM '{node.name}'")
            self.remove_node(node)
        return
    
    def _handle_mouse_motion(self, event) -> None:
        """Handle mouse motion events"""
        if self.is_panning and self.pan_start:
            dx = event.pos[0] - self.pan_start[0]
            dy = event.pos[1] - self.pan_start[1]
            self.pan_offset[0] += dx
            self.pan_offset[1] += dy
            self.pan_start = event.pos
        elif self.dragging_connection:
            self.temp_connection_pos = event.pos
        else:
            canvas_pos = self.screen_to_canvas(event.pos)
            for node in self.nodes:
                if node.dragging:
                    node.move_to(
                        canvas_pos[0] - node.drag_offset[0],
                        canvas_pos[1] - node.drag_offset[1]
                    )
        return
    
    def _delete_selected_nodes(self) -> None:
        """Delete all selected nodes (keyboard shortcut)"""
        for node in self.selected_nodes[:]:
            self.remove_node(node)
        return
    
    def _draw_grid(self, surface) -> None:
        """Draw background grid"""
        scaled_grid_size = int(self.grid_size * self.zoom)
        if scaled_grid_size < self.MIN_GRID_SIZE_DISPLAY:
            return
        offset_x = int(self.pan_offset[0] % scaled_grid_size)
        for x in range(0, self.rect.width, scaled_grid_size):
            draw.line(surface, self.grid_color,
                     (self.rect.x + x + offset_x, self.rect.y),
                     (self.rect.x + x + offset_x, self.rect.bottom))
        offset_y = int(self.pan_offset[1] % scaled_grid_size)
        for y in range(0, self.rect.height, scaled_grid_size):
            draw.line(surface, self.grid_color,
                     (self.rect.x, self.rect.y + y + offset_y),
                     (self.rect.right, self.rect.y + y + offset_y))
        return
    
    def _draw_node(self, surface, node: CanvasNode) -> None:
        """
        Draw a single node with all its components
        
        Args:
            surface: Pygame surface to draw on
            node: Node to draw
        """
        screen_rect = self._node_rect_to_screen(node.rect)
        if node.selected:
            self._draw_node_selection(surface, screen_rect)
        self._draw_node_body(surface, node, screen_rect)
        self._draw_node_header(surface, node, screen_rect)
        self._draw_node_text(surface, node, screen_rect)
        self._draw_connection_points(surface, node)
        return
    
    def _node_rect_to_screen(self, rect: Rect) -> Rect:
        """Convert node rect from canvas to screen coordinates"""
        return Rect(
            rect.x * self.zoom + self.rect.x + self.pan_offset[0],
            rect.y * self.zoom + self.rect.y + self.pan_offset[1],
            rect.width * self.zoom,
            rect.height * self.zoom
        )
    
    def _draw_node_selection(self, surface, screen_rect: Rect) -> None:
        """Draw selection highlight around node"""
        selection_rect = screen_rect.inflate(
            self.NODE_SELECTION_INFLATE, 
            self.NODE_SELECTION_INFLATE
        )
        draw.rect(surface, self.selection_color, selection_rect, 
                 self.NODE_SELECTION_BORDER, 
                 border_radius=self.NODE_SELECTION_RADIUS)
        return
    
    def _draw_node_body(self, surface, node: CanvasNode, screen_rect: Rect) -> None:
        """Draw node background and border"""
        draw.rect(surface, node.color, screen_rect, border_radius=self.NODE_BORDER_RADIUS)
        border_width = (self.NODE_BORDER_WIDTH_SPECIAL 
                       if node.node_type in [NodeType.INPUT, NodeType.OUTPUT] 
                       else self.NODE_BORDER_WIDTH_NORMAL)
        draw.rect(surface, self.NODE_BORDER_COLOR, screen_rect, border_width, 
                 border_radius=self.NODE_BORDER_RADIUS)
        return
    
    def _draw_node_header(self, surface, node: CanvasNode, screen_rect: Rect) -> None:
        """Draw node header bar"""
        header_height = int(node.header_height * self.zoom)
        header_rect = Rect(screen_rect.x, screen_rect.y, screen_rect.width, header_height)
        header_color = tuple(max(0, c - self.HEADER_DARKEN_AMOUNT) for c in node.color)
        draw.rect(surface, header_color, header_rect, 
                 border_top_left_radius=self.NODE_BORDER_RADIUS,
                 border_top_right_radius=self.NODE_BORDER_RADIUS)
        return
    
    def _draw_node_text(self, surface, node: CanvasNode, screen_rect: Rect) -> None:
        """Draw node name and category text"""
        header_height = int(node.header_height * self.zoom)
        header_rect = Rect(screen_rect.x, screen_rect.y, screen_rect.width, header_height)
        scaled_font_size = max(self.MIN_SCALED_FONT, int(self.font_size * self.zoom))
        scaled_font = font.SysFont(None, scaled_font_size)
        name_text = scaled_font.render(node.name, True, self.text_color)
        name_rect = name_text.get_rect(center=(header_rect.centerx, header_rect.centery))
        surface.blit(name_text, name_rect)
        if node.category and node.node_type != NodeType.PROCESS:
            scaled_small_font_size = max(self.MIN_SCALED_TINY_FONT, 
                                        int(self.small_font_size * self.zoom))
            scaled_small_font = font.SysFont(None, scaled_small_font_size)
            cat_text = scaled_small_font.render(node.category, True, self.node_label_color)
            cat_y = screen_rect.y + header_height + int(self.CATEGORY_TEXT_Y_OFFSET * self.zoom)
            cat_rect = cat_text.get_rect(center=(screen_rect.centerx, cat_y))
            surface.blit(cat_text, cat_rect)
        return
    
    def _draw_connection_points(self, surface, node: CanvasNode) -> None:
        """Draw all connection points for a node"""
        point_radius = max(4, int(self.CONNECTION_POINT_RADIUS * self.zoom))
        scaled_tiny_font_size = max(self.MIN_SCALED_TINY_FONT, 
                                   int(self.TINY_FONT_SIZE * self.zoom))
        scaled_tiny_font = font.SysFont(None, scaled_tiny_font_size)
        for name, point in node.input_points.items():
            screen_pos = self.canvas_to_screen(point.position)
            self._draw_connection_point(surface, screen_pos, self.INPUT_POINT_COLOR, 
                                       point_radius, name, scaled_tiny_font, is_input=True)
        for name, point in node.output_points.items():
            screen_pos = self.canvas_to_screen(point.position)
            self._draw_connection_point(surface, screen_pos, self.OUTPUT_POINT_COLOR, 
                                       point_radius, name, scaled_tiny_font, is_input=False)
        return
    
    def _draw_connection_point(self, surface, screen_pos: Tuple[float, float], 
                              color: Tuple[int, int, int], radius: int, 
                              label: str, label_font: font.Font, is_input: bool) -> None:
        """Draw a single connection point with label"""
        draw.circle(surface, color, (int(screen_pos[0]), int(screen_pos[1])), radius)
        draw.circle(surface, self.CONNECTION_POINT_BORDER_COLOR, 
                   (int(screen_pos[0]), int(screen_pos[1])), radius, 
                   self.CONNECTION_POINT_BORDER)
        label_text = label_font.render(label, True, self.node_label_color)
        if is_input:
            label_rect = label_text.get_rect(
                left=screen_pos[0] + radius + self.CONNECTION_POINT_LABEL_OFFSET,
                centery=screen_pos[1]
            )
        else:
            label_rect = label_text.get_rect(
                right=screen_pos[0] - radius - self.CONNECTION_POINT_LABEL_OFFSET,
                centery=screen_pos[1]
            )
        surface.blit(label_text, label_rect)
        return
    
    def _draw_connection(self, surface, connection: Connection) -> None:
        """Draw a connection between nodes"""
        start_pos = connection.get_start_position()
        end_pos = connection.get_end_position()
        if not start_pos or not end_pos:
            return
        start_screen = self.canvas_to_screen(start_pos)
        end_screen = self.canvas_to_screen(end_pos)
        if connection.to_parameter and connection.to_parameter != "image":
            color = self.PARAM_INPUT_POINT_COLOR
        else:
            color = self.selection_color if connection.selected else self.connection_color
        self._draw_bezier_connection(surface, start_screen, end_screen, color)
        return
    
    def _draw_temp_connection(self, surface) -> None:
        """Draw temporary connection while dragging"""
        if not self.dragging_connection or not self.temp_connection_pos:
            return
        from_output = self.dragging_output_name
        output_point = self.dragging_connection.output_points.get(from_output)
        if output_point:
            from_screen = self.canvas_to_screen(output_point.position)
            self._draw_bezier_connection(surface, from_screen, self.temp_connection_pos, 
                                        self.CONNECTION_TEMP_COLOR)
        return
    
    def _draw_bezier_connection(self, surface, start_pos: Tuple[float, float], 
                               end_pos: Tuple[float, float], 
                               color: Tuple[int, int, int]) -> None:
        """Draw a bezier curve connection"""
        dx = end_pos[0] - start_pos[0]
        control_offset = abs(dx) * self.CONNECTION_CONTROL_FACTOR
        control_offset = max(self.CONNECTION_CONTROL_OFFSET_MIN, 
                           min(control_offset, self.CONNECTION_CONTROL_OFFSET_MAX))
        points = []
        for i in range(self.CONNECTION_BEZIER_SEGMENTS + 1):
            t = i / self.CONNECTION_BEZIER_SEGMENTS
            p0 = start_pos
            p1 = (start_pos[0] + control_offset, start_pos[1])
            p2 = (end_pos[0] - control_offset, end_pos[1])
            p3 = end_pos
            x = ((1-t)**3 * p0[0] + 
                 3*(1-t)**2*t * p1[0] + 
                 3*(1-t)*t**2 * p2[0] + 
                 t**3 * p3[0])
            y = ((1-t)**3 * p0[1] + 
                 3*(1-t)**2*t * p1[1] + 
                 3*(1-t)*t**2 * p2[1] + 
                 t**3 * p3[1])
            points.append((int(x), int(y)))
        if len(points) > 1:
            draw.lines(surface, color, False, points, self.CONNECTION_WIDTH)
        return
    
    def _add_default_nodes(self) -> None:
        """Add default input and output nodes to canvas"""
        input_node = CanvasNode(
            "Input",
            "Source",
            self.INPUT_NODE_POS[0],
            self.INPUT_NODE_POS[1],
            color=self.INPUT_NODE_COLOR,
            node_type="input"
        )
        self.nodes.append(input_node)
        output_node = CanvasNode(
            "Output",
            "Destination",
            self.OUTPUT_NODE_POS[0],
            self.OUTPUT_NODE_POS[1],
            color=self.OUTPUT_NODE_COLOR,
            node_type="output"
        )
        output_node.rect.height = self.OUTPUT_NODE_HEIGHT
        output_node.update_connection_points()
        self.nodes.append(output_node)
        return
    
    def _get_node_at_position(self, canvas_pos: Tuple[float, float]) -> Optional[CanvasNode]:
        """Get node at canvas position (topmost node)"""
        for node in reversed(self.nodes):
            if node.contains_point(canvas_pos):
                return node
        return None
    
    def _get_parameter_info(self, node_name: str) -> List[Dict[str, Any]]:
        """Get parameter info for a node type from JSON definitions"""
        for category in self.node_definitions.get('categories', []):
            for node in category.get('nodes', []):
                if node['name'] == node_name:
                    return node.get('parameters', [])
        return []
    
    def _extract_algorithm_inputs(self, pipeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract input parameters from an embedded pipeline"""
        input_params = []
        for conn in pipeline_data.get('connections', []):
            from_node_data = next((n for n in pipeline_data.get('nodes', []) 
                                 if n['id'] == conn['from_node']), None)
            if from_node_data and from_node_data.get('node_type') == 'input':
                param_name = conn.get('to_parameter')
                if param_name and param_name not in [p['name'] for p in input_params]:
                    input_params.append({
                        'name': param_name,
                        'type': 'image',
                        'connectable': True
                    })
        if not input_params:
            input_params.append({'name': 'image', 'type': 'image', 'connectable': True})
        return input_params
    
    def _extract_algorithm_outputs(self, pipeline_data: Dict[str, Any]) -> List[str]:
        """Extract output parameters from an embedded pipeline"""
        output_params = []
        for conn in pipeline_data.get('connections', []):
            to_node_data = next((n for n in pipeline_data.get('nodes', []) 
                               if n['id'] == conn['to_node']), None)
            if to_node_data and to_node_data.get('node_type') == 'output':
                output_name = conn.get('to_parameter', 'image')
                if output_name not in output_params:
                    output_params.append(output_name)
        if not output_params:
            output_params.append('image')
        return output_params