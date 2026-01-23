from pygame import Rect, draw, font, mouse, MOUSEWHEEL, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, K_DELETE, KEYDOWN
from uuid import uuid4
from windows.base_window import BaseWindow

class CanvasNode:
    """Represents a node instance on the canvas"""
    def __init__(self, name, category, x, y, color=(100, 150, 200), parameters=None, parameter_info=None, node_type="process"):
        self.id = str(uuid4())
        self.name = name
        self.category = category
        self.color = color
        self.parameters = parameters or {}
        self.parameter_info = parameter_info or []
        self.node_type = node_type
        self.connectable_params = [p for p in self.parameter_info if p.get('connectable', False)]
        base_height = 80
        param_spacing = 20
        if node_type == "output":
            total_height = base_height + param_spacing
        else:
            total_height = base_height + len(self.connectable_params) * param_spacing
        self.rect = Rect(x, y, 150, total_height)
        self.header_height = 30
        self.input_point = None
        self.input_label = None
        self.output_points = {}
        self.param_input_points = {}
        self.update_connection_points()
        self.selected = False
        self.dragging = False
        self.drag_offset = (0, 0)
        return
        
    def update_connection_points(self):
        """Update input/output connection point positions"""
        if self.node_type == "input":
            self.input_point = None
            self.input_label = None
            self.output_points = {"image": (self.rect.right, self.rect.centery)}
            self.param_input_points = {}
        elif self.node_type == "output":
            self.input_point = (self.rect.left, self.rect.centery)
            self.input_label = "image"
            self.output_points = {}
            self.param_input_points = {}
            y_offset_input = self.rect.top + self.header_height + 40
            self.param_input_points["data"] = (self.rect.left, y_offset_input)
        else:
            self.input_point = (self.rect.left, self.rect.top + self.header_height + 10)
            self.input_label = "image"
            self.output_points = {}
            y_offset = self.rect.top + self.header_height + 10
            self.output_points["image"] = (self.rect.right, y_offset)
            y_offset += 20
            if self.name == "Object Characteristics":
                self.output_points["data"] = (self.rect.right, y_offset)
                y_offset += 20
            self.param_input_points = {}
            y_offset_input = self.rect.top + self.header_height + 30
            for param in self.connectable_params:
                param_name = param['name']
                self.param_input_points[param_name] = (self.rect.left, y_offset_input)
                y_offset_input += 25
        return
    
    def contains_point(self, pos):
        """Check if a point is inside this node"""
        return self.rect.collidepoint(pos)
    
    def is_near_input(self, pos, threshold=15):
        """Check if position is near main input connection point"""
        if self.input_point:
            dx = pos[0] - self.input_point[0]
            dy = pos[1] - self.input_point[1]
            return (dx*dx + dy*dy) < threshold*threshold
        return False
    
    def is_near_param_input(self, pos, threshold=15):
        """Check if position is near any parameter input. Returns parameter name or None"""
        for param_name, point in self.param_input_points.items():
            dx = pos[0] - point[0]
            dy = pos[1] - point[1]
            if (dx*dx + dy*dy) < threshold*threshold:
                return param_name
        return None
    
    def is_near_output(self, pos, threshold=15):
        """Check if position is near any output connection point. Returns output name or None"""
        for output_name, point in self.output_points.items():
            dx = pos[0] - point[0]
            dy = pos[1] - point[1]
            if (dx*dx + dy*dy) < threshold*threshold:
                return output_name
        return None

class Connection:
    """Represents a connection between two nodes"""
    def __init__(self,from_node,to_node,to_parameter=None,from_output="image"):
        self.id = str(uuid4())
        self.from_node = from_node
        self.to_node = to_node
        self.to_parameter = to_parameter
        self.from_output = from_output
        self.color = (150, 150, 150)
        self.selected = False
        return

class NodeCanvas(BaseWindow):
    """Visual programming canvas for connecting nodes"""
    def __init__(self,
                 rel_pos=(0.251, 0.051),
                 rel_size=(0.498, 0.608),
                 reference_resolution=(1920, 1080),
                 background_color=(30, 30, 30),
                 grid_color=(50, 50, 50),
                 text_color=(0, 0, 0),
                 selection_color=(255, 200, 0),
                 connection_color=(150, 150, 150),
                 node_definitions=None):
        super().__init__(rel_pos, rel_size, reference_resolution, background_color)
        self.base_font_size = 20
        self.base_small_font_size = 16
        self.grid_color = grid_color
        self.text_color = text_color
        self.selection_color = selection_color
        self.connection_color = connection_color
        self.node_label_color = (0,0,0)
        self.small_font = None
        self.node_definitions = node_definitions or {"categories": []}
        self.nodes = []
        self.connections = []
        self.selected_nodes = []
        self.dragging_node = None
        self.dragging_connection = None
        self.temp_connection_pos = None
        self.pan_offset = [0, 0]
        self.is_panning = False
        self.pan_start = None
        self.zoom = 1.0
        self.min_zoom = 0.3
        self.max_zoom = 3.0
        self.zoom_step = 0.1
        self.grid_size = 20
        self.show_grid = True
        self._add_default_nodes()
        return
    
    def update_layout(self, window_size):
        """Update canvas size and position"""
        super().update_layout(window_size)
        scale_factor = self.get_scale_factor()
        self.small_font_size = max(14, int(16 * scale_factor))
        self.small_font = font.SysFont(None, self.small_font_size)
        return
    
    def handle_events(self, events):
        """Handle user input"""
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
                    for node in self.selected_nodes[:]:
                        self.remove_node(node)
        return
    
    def update(self):
        """Update canvas state"""
        pass
    
    def draw(self, surface):
        """Draw the canvas"""
        draw.rect(surface, self.background_color, self.rect)
        clip_rect = surface.get_clip()
        surface.set_clip(self.rect)
        if self.show_grid:
            self._draw_grid(surface)
        for connection in self.connections:
            self._draw_connection(surface, connection)
        if self.dragging_connection and self.temp_connection_pos:
            from_output = getattr(self, 'dragging_output_name', 'output')
            from_point = self.dragging_connection.output_points.get(from_output)
            if from_point:
                from_screen = self.canvas_to_screen(from_point)
                self._draw_bezier_connection(surface, from_screen, self.temp_connection_pos, (200, 200, 100))
        for node in self.nodes:
            self._draw_node(surface, node)
        draw.rect(surface, (100, 100, 100), self.rect, 2)
        surface.set_clip(clip_rect)
        return
    
    def _handle_zoom(self, event):
        """Handle mouse wheel zoom"""
        mouse_pos = mouse.get_pos()
        old_canvas_pos = self.screen_to_canvas(mouse_pos)
        
        if event.y > 0:
            self.zoom = min(self.max_zoom, self.zoom + self.zoom_step)
        else:
            self.zoom = max(self.min_zoom, self.zoom - self.zoom_step)
        
        new_canvas_pos = self.screen_to_canvas(mouse_pos)
        self.pan_offset[0] += (new_canvas_pos[0] - old_canvas_pos[0]) * self.zoom
        self.pan_offset[1] += (new_canvas_pos[1] - old_canvas_pos[1]) * self.zoom
        return
    
    def _handle_mouse_down(self, event):
        """Handle mouse button down events"""
        canvas_pos = self.screen_to_canvas(event.pos)
        if event.button == 1:
            for node in self.nodes:
                output_name = node.is_near_output(canvas_pos)
                if output_name:
                    self.dragging_connection = node
                    self.dragging_output_name = output_name
                    self.temp_connection_pos = event.pos
                    return
            clicked_node = self.get_node_at_position(canvas_pos)
            if clicked_node:
                clicked_node.dragging = True
                clicked_node.drag_offset = (
                    canvas_pos[0] - clicked_node.rect.x,
                    canvas_pos[1] - clicked_node.rect.y
                )
                if clicked_node not in self.selected_nodes:
                    self.selected_nodes = [clicked_node]
                    clicked_node.selected = True
                    for node in self.nodes:
                        if node != clicked_node:
                            node.selected = False
            else:
                self.is_panning = True
                self.pan_start = event.pos
                for node in self.nodes:
                    node.selected = False
                self.selected_nodes = []
        return
    
    def _handle_left_mouse_up(self, event):
        """Handle left mouse button up"""
        for node in self.nodes:
            node.dragging = False
        if self.dragging_connection:
            canvas_pos = self.screen_to_canvas(event.pos)
            from_output = getattr(self, 'dragging_output_name', 'output')
            for node in self.nodes:
                if node == self.dragging_connection:
                    continue
                if node.input_point and node.is_near_input(canvas_pos):
                    self.add_connection(self.dragging_connection, node, None, from_output)
                    break
                param_name = node.is_near_param_input(canvas_pos)
                if param_name:
                    self.add_connection(self.dragging_connection, node, param_name, from_output)
                    break
            self.dragging_connection = None
            self.dragging_output_name = None
            self.temp_connection_pos = None
        return
    
    def _handle_right_mouse_up(self, event):
        """Handle right mouse button up (delete connections/nodes)"""
        canvas_pos = self.screen_to_canvas(event.pos)
        clicked_node = self.get_node_at_position(canvas_pos)
        if clicked_node:
            node_left = clicked_node.rect.x
            node_width = clicked_node.rect.width
            click_x = canvas_pos[0]
            relative_x = click_x - node_left
            third = relative_x / node_width
            if third < 0.33:
                connections_to_remove = [c for c in self.connections if c.to_node == clicked_node]
                for conn in connections_to_remove:
                    self.remove_connection(conn)
                    print(f"Deleted connection TO '{clicked_node.name}'")
            elif third > 0.67:
                connections_to_remove = [c for c in self.connections if c.from_node == clicked_node]
                for conn in connections_to_remove:
                    self.remove_connection(conn)
                    print(f"Deleted connection FROM '{clicked_node.name}'")
            else:
                self.remove_node(clicked_node)
        return
    
    def _handle_mouse_motion(self, event):
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
                    node.rect.x = canvas_pos[0] - node.drag_offset[0]
                    node.rect.y = canvas_pos[1] - node.drag_offset[1]
                    node.update_connection_points()
        return
    
    def _add_default_nodes(self):
        """Add default input and output nodes to the canvas"""
        input_node = CanvasNode(
            "Input",
            "Source",
            50,
            100,
            color=(50, 180, 100),
            node_type="input"
        )
        self.nodes.append(input_node)
        output_node = CanvasNode(
            "Output",
            "Destination",
            500,
            100,
            color=(180, 50, 50),
            node_type="output"
        )
        output_node.rect.height = 100
        output_node.update_connection_points()
        self.nodes.append(output_node)
        return
    
    def screen_to_canvas(self, screen_pos):
        """Convert screen position to canvas position"""
        return (
            (screen_pos[0] - self.rect.x - self.pan_offset[0]) / self.zoom,
            (screen_pos[1] - self.rect.y - self.pan_offset[1]) / self.zoom
        )

    def canvas_to_screen(self, canvas_pos):
        """Convert canvas position to screen position"""
        return (
            canvas_pos[0] * self.zoom + self.rect.x + self.pan_offset[0],
            canvas_pos[1] * self.zoom + self.rect.y + self.pan_offset[1]
        )
    
    def add_node_from_template(self, template, screen_pos):
        """Add a node to the canvas from a template at screen position"""
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
    
    def add_algorithm_node(self, algorithm_name, algorithm_data, screen_pos, color=(150, 100, 200)):
        """Add a single algorithm node that encapsulates a pipeline"""
        canvas_pos = self.screen_to_canvas(screen_pos)
        # Extract input and output parameters from the pipeline
        input_params = []
        output_params = []
        pipeline_data = algorithm_data.get('pipeline_data', {})
        # Find connections to/from input and output nodes in the embedded pipeline
        for conn in pipeline_data.get('connections', []):
            # Find nodes by ID
            from_node_data = next((n for n in pipeline_data.get('nodes', []) if n['id'] == conn['from_node']), None)
            to_node_data = next((n for n in pipeline_data.get('nodes', []) if n['id'] == conn['to_node']), None)
            # Track parameters that come from the input node (these become algorithm inputs)
            if from_node_data and from_node_data.get('node_type') == 'input':
                param_name = conn.get('to_parameter')
                if param_name and param_name not in [p['name'] for p in input_params]:
                    input_params.append({
                        'name': param_name,
                        'type': 'image',
                        'connectable': True
                    })
            # Track outputs going to the output node (these become algorithm outputs)
            if to_node_data and to_node_data.get('node_type') == 'output':
                output_name = conn.get('to_parameter', 'image')
                if output_name not in output_params:
                    output_params.append(output_name)
        # Ensure at least basic image input/output
        if not input_params:
            input_params.append({'name': 'image', 'type': 'image', 'connectable': True})
        if not output_params:
            output_params.append('image')
        # Create the algorithm node
        new_node = CanvasNode(
            algorithm_name,
            "Algorithm",
            canvas_pos[0] - 75,
            canvas_pos[1] - 40,
            color,
            {},  # No editable parameters for algorithm nodes
            input_params,
            node_type="algorithm"
        )
        # Store the pipeline data in the node
        new_node.pipeline_data = pipeline_data
        new_node.algorithm_outputs = output_params
        # Recalculate connection points with the new data
        new_node.update_connection_points()
        self.nodes.append(new_node)
        print(f"Added algorithm node '{algorithm_name}' to canvas")
        return new_node

    def _get_parameter_info(self, node_name):
        """Get full parameter info for a node type from JSON definitions"""
        for category in self.node_definitions.get('categories', []):
            for node in category.get('nodes', []):
                if node['name'] == node_name:
                    return node.get('parameters', [])
        return []
    
    def _get_default_parameters(self, node_name):
        """Get default parameters for a node type from JSON definitions"""
        param_info = self._get_parameter_info(node_name)
        params = {}
        for param in param_info:
            params[param['name']] = param['value']
        return params
    
    def remove_node(self, node):
        """Remove a node and all its connections"""
        if node.node_type in ["input", "output"]:
            print(f"Cannot delete {node.node_type} node")
            return
        self.connections = [c for c in self.connections 
                          if c.from_node != node and c.to_node != node]
        if node in self.nodes:
            self.nodes.remove(node)
        if node in self.selected_nodes:
            self.selected_nodes.remove(node)
        return
    
    def add_connection(self,from_node,to_node,to_parameter=None,from_output="image"):
        """Add a connection between two nodes"""
        for conn in self.connections:
            if conn.from_node == from_node and conn.to_node == to_node and conn.to_parameter == to_parameter and conn.from_output == from_output:
                print(f"Connection already exists")
                return None
        if from_node == to_node:
            print(f"Cannot connect node to itself")
            return None
        if from_output not in from_node.output_points:
            print(f"Cannot connect from {from_node.name}: output '{from_output}' not found")
            return None
        if to_parameter:
            if to_parameter not in to_node.param_input_points:
                print(f"Cannot connect to {to_node.name}: parameter '{to_parameter}' not found")
                return None
        else:
            if to_node.input_point is None:
                print(f"Cannot connect to {to_node.name}: no input")
                return None
        connection = Connection(from_node, to_node, to_parameter, from_output)
        self.connections.append(connection)
        if to_parameter:
            print(f"Connected '{from_node.name}.{from_output}' to '{to_node.name}.{to_parameter}'")
        else:
            print(f"Connected '{from_node.name}.{from_output}' to '{to_node.name}'")
        return connection
    
    def remove_connection(self, connection):
        """Remove a connection"""
        if connection in self.connections:
            self.connections.remove(connection)
        return
    
    def get_node_at_position(self, canvas_pos):
        """Get node at canvas position (topmost node)"""
        for node in reversed(self.nodes):
            if node.contains_point(canvas_pos):
                return node
        return None
    
    def get_selected_node(self):
        """Get the currently selected node (for parameter editing)"""
        if self.selected_nodes:
            selected = self.selected_nodes[0]
            if selected.node_type == "process":
                return selected
        return None
    
    def _draw_grid(self, surface):
        """Draw background grid"""
        scaled_grid_size = int(self.grid_size * self.zoom)
        if scaled_grid_size < 5:
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
    
    def _draw_node(self, surface, node):
        """Draw a single node"""
        screen_rect = Rect(
            node.rect.x * self.zoom + self.rect.x + self.pan_offset[0],
            node.rect.y * self.zoom + self.rect.y + self.pan_offset[1],
            node.rect.width * self.zoom,
            node.rect.height * self.zoom
        )
        if node.selected:
            draw.rect(surface, self.selection_color, screen_rect.inflate(4, 4), 3, border_radius=8)
        draw.rect(surface, node.color, screen_rect, border_radius=5)
        border_width = 3 if node.node_type in ["input", "output"] else 2
        draw.rect(surface, (200, 200, 200), screen_rect, border_width, border_radius=5)
        header_height = int(node.header_height * self.zoom)
        header_rect = Rect(screen_rect.x, screen_rect.y, screen_rect.width, header_height)
        draw.rect(surface, tuple(max(0, c - 30) for c in node.color), header_rect, border_top_left_radius=5, border_top_right_radius=5)
        scaled_font_size = max(8, int(self.font_size * self.zoom))
        scaled_font = font.SysFont(None, scaled_font_size)
        name_text = scaled_font.render(node.name, True, self.text_color)
        name_rect = name_text.get_rect(center=(header_rect.centerx, header_rect.centery))
        surface.blit(name_text, name_rect)
        if node.category and node.node_type != "process":
            scaled_small_font_size = max(6, int(self.small_font_size * self.zoom))
            scaled_small_font = font.SysFont(None, scaled_small_font_size)
            cat_text = scaled_small_font.render(node.category, True, self.node_label_color)
            cat_rect = cat_text.get_rect(center=(screen_rect.centerx, screen_rect.y + header_height + int(15 * self.zoom)))
            surface.blit(cat_text, cat_rect)
        point_radius = max(4, int(8 * self.zoom))
        if node.input_point:
            input_screen = self.canvas_to_screen(node.input_point)
            draw.circle(surface, (100, 200, 100), input_screen, point_radius)
            draw.circle(surface, (50, 50, 50), input_screen, point_radius, 2)
            if hasattr(node, 'input_label') and node.input_label:
                scaled_tiny_font_size = max(6, int(12 * self.zoom))
                scaled_tiny_font = font.SysFont(None, scaled_tiny_font_size)
                input_text = scaled_tiny_font.render(node.input_label, True, self.node_label_color)
                input_text_rect = input_text.get_rect(left=input_screen[0] + point_radius + 5, centery=input_screen[1])
                surface.blit(input_text, input_text_rect)
        if node.param_input_points:
            scaled_tiny_font_size = max(6, int(12 * self.zoom))
            scaled_tiny_font = font.SysFont(None, scaled_tiny_font_size)
            for param_name, point in node.param_input_points.items():
                param_screen = self.canvas_to_screen(point)
                draw.circle(surface, (100, 150, 200), param_screen, point_radius)
                draw.circle(surface, (50, 50, 50), param_screen, point_radius, 2)
                param_text = scaled_tiny_font.render(param_name, True, self.node_label_color)
                param_text_rect = param_text.get_rect(left=param_screen[0] + point_radius + 5, centery=param_screen[1])
                surface.blit(param_text, param_text_rect)
        if node.output_points:
            scaled_tiny_font_size = max(6, int(12 * self.zoom))
            scaled_tiny_font = font.SysFont(None, scaled_tiny_font_size)
            for output_name, point in node.output_points.items():
                output_screen = self.canvas_to_screen(point)
                draw.circle(surface, (200, 100, 100), output_screen, point_radius)
                draw.circle(surface, (50, 50, 50), output_screen, point_radius, 2)
                output_text = scaled_tiny_font.render(output_name, True, self.node_label_color)
                output_text_rect = output_text.get_rect(right=output_screen[0] - point_radius - 5, centery=output_screen[1])
                surface.blit(output_text, output_text_rect)
        return
    
    def _draw_connection(self, surface, connection):
        """Draw a connection between nodes"""
        from_output = connection.from_output if hasattr(connection, 'from_output') else "output"
        from_point = connection.from_node.output_points.get(from_output)
        if not from_point:
            return
        from_screen = self.canvas_to_screen(from_point)
        if connection.to_parameter:
            to_point = connection.to_node.param_input_points.get(connection.to_parameter)
            if not to_point:
                return
            to_screen = self.canvas_to_screen(to_point)
            color = (100, 150, 200) if not connection.selected else self.selection_color
        else:
            to_screen = self.canvas_to_screen(connection.to_node.input_point)
            color = self.selection_color if connection.selected else self.connection_color
        self._draw_bezier_connection(surface, from_screen, to_screen, color)
        return
    
    def _draw_bezier_connection(self, surface, start_pos, end_pos, color):
        """Draw a bezier curve connection"""
        dx = end_pos[0] - start_pos[0]
        control_offset = abs(dx) * 0.5
        control_offset = max(50, min(control_offset, 200))
        num_segments = 20
        points = []
        for i in range(num_segments + 1):
            t = i / num_segments
            p0 = start_pos
            p1 = (start_pos[0] + control_offset, start_pos[1])
            p2 = (end_pos[0] - control_offset, end_pos[1])
            p3 = end_pos
            x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
            y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
            points.append((int(x), int(y)))
        if len(points) > 1:
            draw.lines(surface, color, False, points, 3)
        return