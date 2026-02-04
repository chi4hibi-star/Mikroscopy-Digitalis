from pygame import VIDEORESIZE, MOUSEBUTTONUP, Rect, draw, font
from pathlib import Path
from json import load, dump
from tkinter import Tk, filedialog
from traceback import print_exc
from windows.node_library import TabbedNodeViewer
from windows.parameter_panel import ParameterPanel
from windows.node_canvas import NodeCanvas, CanvasNode
from windows.menu_bar import MenuBar
from typing import Tuple, Dict, List, Any, Optional

class AlgorithmScene:
    """
    Visual node-based algorithm/pipeline editor scene
    
    Features:
    - Drag-and-drop node placement from library
    - Visual connection system for building pipelines
    - Parameter editing for selected nodes
    - Save/load pipelines as JSON
    - Reusable algorithm nodes (saved pipelines as nodes)
    - Pan and zoom canvas
    """
    
    # File paths
    NODE_DEFINITIONS_FILE = "nodes_definition.json"
    PIPELINES_DIR = "pipelines"
    
    def __init__(self, screen, settings, switch_scene_callback):
        """
        Initialize the Algorithm Scene
        
        Args:
            screen: Pygame display surface
            settings: Settings instance
            switch_scene_callback: Callback to switch between scenes
        """
        self.settings = settings
        self.switch_scene_callback = switch_scene_callback
        self.window_width, self.window_height = screen.get_size()
        self.node_definitions = self._load_node_definitions()
        self.algorithm_definitions = self._load_algorithm_definitions()
        self.setup_working_directory()
        self.setup_menu_bar()
        self.setup_node_viewer()
        self.setup_algorithm_viewer()
        self.setup_canvas()
        self.setup_parameter_panel()
        self.update_layout(self.window_width, self.window_height)
        self._last_selected_node = None
        return
    
    def setup_working_directory(self):
        """Setup working directory for saved pipelines"""
        self.working_dir = Path.cwd() / self.PIPELINES_DIR
        if not self.working_dir.exists():
            self.working_dir.mkdir(parents=True)
            print(f"Pipeline directory created: {self.working_dir}")
        return
    
    def setup_menu_bar(self):
        """Setup the menu bar with save/load callbacks"""
        self.menu_bar = MenuBar(
            scene_instance=self,
            scene="algorithms",
            rel_pos=(0.0, 0.0),
            rel_size=(1.0, 0.05),
            switch_scene_callback=self.switch_scene_callback,
            call_methods=[self._load_pipeline, self._save_pipeline],
            reference_resolution=self.settings.saved_settings["display"]["resolution"]
        )
        return
    
    def setup_node_viewer(self):
        """Setup the tabbed node viewer from JSON definitions"""
        self.node_viewer = TabbedNodeViewer(
            rel_pos=(0.001, 0.051),
            rel_size=(0.248, 0.948),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            node_color=(100, 150, 200),
            node_hover_color=(120, 170, 220),
            text_color=(255, 255, 255)
        )
        for category in self.node_definitions.get('categories', []):
            category_name = category.get('name', 'Unknown')
            self.node_viewer.add_category(category_name)
            for node in category.get('nodes', []):
                node_name = node.get('name', 'Unnamed')
                description = node.get('description', '')
                color = tuple(node.get('color', [100, 150, 200]))
                self.node_viewer.add_node(node_name, category_name, description, color)
        return
    
    def setup_algorithm_viewer(self):
        """Setup the algorithm viewer for saved pipelines"""
        self.algorithm_viewer = TabbedNodeViewer(
            rel_pos=(0.751, 0.051),
            rel_size=(0.248, 0.948),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            node_color=(150, 100, 200),
            node_hover_color=(170, 120, 220),
            text_color=(255, 255, 255)
        )
        for category in self.algorithm_definitions.get('categories', []):
            category_name = category.get('name', 'Unknown')
            self.algorithm_viewer.add_category(category_name)
            for algorithm in category.get('algorithms', []):
                algorithm_name = algorithm.get('name', 'Unnamed')
                description = algorithm.get('description', '')
                color = tuple(algorithm.get('color', [150, 100, 200]))
                self.algorithm_viewer.add_node(algorithm_name, category_name, description, color)
        return
    
    def setup_canvas(self):
        """Setup the visual programming canvas"""
        self.canvas = NodeCanvas(
            rel_pos=(0.251, 0.051),
            rel_size=(0.498, 0.608),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            grid_color=(50, 50, 50),
            text_color=(255, 255, 255),
            selection_color=(255, 200, 0),
            connection_color=(150, 150, 150),
            node_definitions=self.node_definitions
        )
        return
    
    def setup_parameter_panel(self):
        """Setup the parameter editing panel"""
        self.parameter_panel = ParameterPanel(
            rel_pos=(0.251, 0.661),
            rel_size=(0.498, 0.338),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            header_color=(60, 60, 60),
            text_color=(255, 255, 255),
            param_bg_color=(50, 50, 50)
        )
        return
    
    def update_layout(self, width: int, height: int):
        """
        Update all window layouts when window is resized
        
        Args:
            width: New window width
            height: New window height
        """
        self.menu_bar.update_layout((width, height))
        self.node_viewer.update_layout((width, height))
        self.algorithm_viewer.update_layout((width, height))
        self.canvas.update_layout((width, height))
        self.parameter_panel.update_layout((width, height))
        return
    
    def handle_events(self, events: list):
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout(event.w, event.h)
            if event.type == MOUSEBUTTONUP and event.button == 1:
                dragging_node, mouse_pos = self.node_viewer.get_dragging_node()
                if dragging_node and self.canvas.rect.collidepoint(mouse_pos):
                    new_node = self.canvas.add_node_from_template(dragging_node, mouse_pos)
                    if new_node:
                        self._update_parameter_panel_for_node(new_node)
                self.node_viewer.stop_dragging()
                dragging_algorithm, mouse_pos = self.algorithm_viewer.get_dragging_node()
                if dragging_algorithm and self.canvas.rect.collidepoint(mouse_pos):
                    self._add_algorithm_node(dragging_algorithm, mouse_pos)
                self.algorithm_viewer.stop_dragging()
        self.menu_bar.handle_events(events)
        self.node_viewer.handle_events(events)
        self.algorithm_viewer.handle_events(events)
        self.canvas.handle_events(events)
        self.parameter_panel.handle_events(events)
        return
    
    def update(self):
        """Update scene state every frame"""
        self.algorithm_viewer.update()
        self.node_viewer.update()
        self.canvas.update()
        self.parameter_panel.update()
        selected_node = self.canvas.get_selected_node()
        if selected_node:
            if not hasattr(self, '_last_selected_node') or self._last_selected_node != selected_node:
                self._update_parameter_panel_for_node(selected_node)
                self._last_selected_node = selected_node
        else:
            if hasattr(self, '_last_selected_node') and self._last_selected_node is not None:
                self.parameter_panel.clear_selection()
                self._last_selected_node = None
        return
    
    def draw(self, screen):
        """
        Draw all windows to the screen
        
        Args:
            screen: Pygame surface to draw on
        """
        self.menu_bar.draw(screen)
        self.node_viewer.draw(screen)
        self.algorithm_viewer.draw(screen)
        self.canvas.draw(screen)
        self.parameter_panel.draw(screen)
        self._draw_dragging_node(self.node_viewer.get_dragging_node(), screen)
        self._draw_dragging_node(self.algorithm_viewer.get_dragging_node(), screen)
        return
    
    def on_scene_enter(self):
        """Called when this scene becomes active"""
        pass
    
    def cleanup(self):
        """Cleanup scene resources"""
        pass
    
    def _add_algorithm_node(self, algorithm_template, mouse_pos: Tuple[int, int]):
        """
        Add a single algorithm node that encapsulates a pipeline
        
        Args:
            algorithm_template: NodeTemplate with algorithm information
            mouse_pos: Mouse position where node should be created
        """
        try:
            algorithm_data = None
            for category in self.algorithm_definitions.get('categories', []):
                for algorithm in category.get('algorithms', []):
                    if algorithm['name'] == algorithm_template.name:
                        algorithm_data = algorithm
                        break
                if algorithm_data:
                    break
            if not algorithm_data:
                print(f"Could not find algorithm data for {algorithm_template.name}")
                return
            new_node = self.canvas.add_algorithm_node(
                algorithm_template.name,
                algorithm_data,
                mouse_pos,
                algorithm_template.color
            )
            if new_node:
                print(f"Added algorithm node '{algorithm_template.name}'")
        except Exception as e:
            print(f"Error adding algorithm node: {e}")
            print_exc()
        return
    
    def _update_parameter_panel_for_node(self, node: CanvasNode):
        """
        Update parameter panel with the selected node's parameters
        
        Args:
            node: The selected canvas node
        """
        if node.node_type.value == "algorithm":
            self.parameter_panel.set_selected_node(node, node.name, [])
            return
        params = self._get_parameter_definitions(node.name)
        for param in params:
            param_name = param['name']
            if param_name in node.parameters:
                value = node.parameters[param_name]
                if param['type'] == 'int':
                    param['value'] = int(value) if not isinstance(value, int) else value
                elif param['type'] == 'float':
                    param['value'] = float(value) if not isinstance(value, float) else value
                elif param['type'] == 'bool':
                    param['value'] = bool(value) if not isinstance(value, bool) else value
                else:
                    param['value'] = value
        self.parameter_panel.set_selected_node(node, node.name, params)
        return
    
    def _get_parameter_definitions(self, node_name: str) -> List[Dict[str, Any]]:
        """
        Get parameter definitions for a node type from JSON
        
        Args:
            node_name: Name of the node type
            
        Returns:
            List of parameter definition dictionaries
        """
        for category in self.node_definitions.get('categories', []):
            for node in category.get('nodes', []):
                if node['name'] == node_name:
                    return node.get('parameters', [])
        return []
    
    def _draw_dragging_node(self, drag_data: Tuple[Any, Optional[Tuple[int, int]]], screen):
        """
        Draw a node being dragged from the library
        
        Args:
            drag_data: Tuple of (dragging_node, mouse_pos)
            screen: Pygame surface to draw on
        """
        dragging_node, mouse_pos = drag_data
        if not dragging_node or not mouse_pos:
            return
        drag_rect = Rect(mouse_pos[0] - 75, mouse_pos[1] - 30, 150, 60)
        draw.rect(screen, (*dragging_node.color, 150), drag_rect, border_radius=5)
        draw.rect(screen, (255, 255, 255), drag_rect, 2, border_radius=5)
        drag_font = font.SysFont(None, 20)
        drag_text = drag_font.render(dragging_node.name, True, (255, 255, 255))
        text_rect = drag_text.get_rect(center=drag_rect.center)
        screen.blit(drag_text, text_rect)
        return
    
    def _load_node_definitions(self) -> Dict[str, Any]:
        """
        Load node definitions from JSON file
        
        Returns:
            Dictionary with node definitions or empty structure if error
        """
        try:
            json_path = Path(self.NODE_DEFINITIONS_FILE)
            if not json_path.exists():
                print(f"Warning: {self.NODE_DEFINITIONS_FILE} not found, using empty definitions")
                return {"categories": []}
            with open(json_path, 'r') as f:
                data = load(f)
                print(f"Loaded {len(data.get('categories', []))} node categories from JSON")
                return data
        except Exception as e:
            print(f"Error loading node definitions: {e}")
            return {"categories": []}
    
    def _load_algorithm_definitions(self) -> Dict[str, Any]:
        """
        Load saved pipelines as algorithm definitions
        
        Returns:
            Dictionary with algorithm definitions or empty structure if error
        """
        try:
            pipeline_dir = Path.cwd() / self.PIPELINES_DIR
            if not pipeline_dir.exists():
                print("Warning: No pipeline directory found, using empty definitions")
                return {"categories": []}
            pipeline_files = list(pipeline_dir.glob("*.json"))
            if not pipeline_files:
                print("No saved pipelines found")
                return {"categories": []}
            algorithms = []
            for pipeline_file in pipeline_files:
                try:
                    with open(pipeline_file, 'r') as f:
                        pipeline_data = load(f)
                    algorithm = {
                        "name": pipeline_file.stem,
                        "description": f"Saved pipeline: {pipeline_file.name}",
                        "color": [150, 100, 200],
                        "pipeline_data": pipeline_data
                    }
                    algorithms.append(algorithm)
                    print(f"Loaded pipeline: {pipeline_file.name}")
                except Exception as e:
                    print(f"Error loading pipeline {pipeline_file.name}: {e}")
                    continue
            return {
                "categories": [
                    {
                        "name": "Saved Algorithms",
                        "algorithms": algorithms
                    }
                ]
            }
        except Exception as e:
            print(f"Error loading saved pipelines: {e}")
            return {"categories": []}
    
    def _load_pipeline(self):
        """Load a pipeline from JSON file"""
        try:
            root = Tk()
            root.withdraw()
            initial_dir = str(self.working_dir) if self.working_dir.exists() else None
            filepath = filedialog.askopenfilename(
                title="Load Pipeline",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=initial_dir
            )
            root.destroy()
            if not filepath:
                return
            with open(filepath, 'r') as f:
                pipeline_data = load(f)
            self._deserialize_pipeline(pipeline_data)
            print(f"Pipeline loaded from: {filepath}")
        except Exception as e:
            print(f"Error loading pipeline: {e}")
            print_exc()
        return
    
    def _save_pipeline(self):
        """Save the current pipeline to JSON file"""
        try:
            root = Tk()
            root.withdraw()
            initial_dir = str(self.working_dir) if self.working_dir.exists() else None
            filepath = filedialog.asksaveasfilename(
                title="Save Pipeline",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=initial_dir
            )
            root.destroy()
            if not filepath:
                return
            pipeline_data = self._serialize_pipeline()
            with open(filepath, 'w') as f:
                dump(pipeline_data, f, indent=2)
            print(f"Pipeline saved to: {filepath}")
            self.algorithm_definitions = self._load_algorithm_definitions()
            self.algorithm_viewer.categories.clear()
            self.algorithm_viewer.nodes.clear()
            for category in self.algorithm_definitions.get('categories', []):
                category_name = category.get('name', 'Unknown')
                self.algorithm_viewer.add_category(category_name)
                for algorithm in category.get('algorithms', []):
                    algorithm_name = algorithm.get('name', 'Unnamed')
                    description = algorithm.get('description', '')
                    color = tuple(algorithm.get('color', [150, 100, 200]))
                    self.algorithm_viewer.add_node(algorithm_name, category_name, description, color)
        except Exception as e:
            print(f"Error saving pipeline: {e}")
            print_exc()
        return
    
    def _serialize_pipeline(self) -> Dict[str, Any]:
        """
        Convert the current pipeline to a JSON-serializable format
        
        Returns:
            Dictionary representing the pipeline
        """
        pipeline = {
            "version": "1.0",
            "nodes": [],
            "connections": []
        }
        node_id_map = {}
        for idx, node in enumerate(self.canvas.nodes):
            node_id = f"node_{idx}"
            node_id_map[node.id] = node_id
            node_data = {
                "id": node_id,
                "name": node.name,
                "category": node.category,
                "node_type": node.node_type.value,
                "position": [node.rect.x, node.rect.y],
                "color": list(node.color),
                "parameters": node.parameters.copy()
            }
            if node.node_type.value == "algorithm":
                node_data["pipeline_data"] = getattr(node, "pipeline_data", {})
                node_data["algorithm_outputs"] = getattr(node, "algorithm_outputs", ["image"])
            pipeline["nodes"].append(node_data)
        for conn in self.canvas.connections:
            conn_data = {
                "from_node": node_id_map[conn.from_node.id],
                "to_node": node_id_map[conn.to_node.id],
                "to_parameter": conn.to_parameter,
                "from_output": conn.from_output
            }
            pipeline["connections"].append(conn_data)
        return pipeline
    
    def _deserialize_pipeline(self, pipeline_data: Dict[str, Any]):
        """
        Load a pipeline from JSON data
        
        Args:
            pipeline_data: Dictionary containing serialized pipeline
        """
        nodes_to_remove = [n for n in self.canvas.nodes 
                          if n.node_type.value in ["process", "algorithm"]]
        for node in nodes_to_remove:
            self.canvas.remove_node(node)
        node_map = {}
        for node in self.canvas.nodes:
            if node.node_type.value == "input":
                for node_data in pipeline_data.get("nodes", []):
                    if node_data.get("node_type") == "input":
                        node.rect.x = node_data["position"][0]
                        node.rect.y = node_data["position"][1]
                        node.update_connection_points()
                        node_map[node_data["id"]] = node
                        break
            elif node.node_type.value == "output":
                for node_data in pipeline_data.get("nodes", []):
                    if node_data.get("node_type") == "output":
                        node.rect.x = node_data["position"][0]
                        node.rect.y = node_data["position"][1]
                        node.rect.height = 100
                        node.update_connection_points()
                        node_map[node_data["id"]] = node
                        break
        for node_data in pipeline_data.get("nodes", []):
            if node_data.get("node_type") == "algorithm":
                pipeline_data_embedded = node_data.get("pipeline_data", {})
                input_params = []
                for conn in pipeline_data_embedded.get("connections", []):
                    from_node_data = next((n for n in pipeline_data_embedded.get("nodes", []) 
                                         if n['id'] == conn['from_node']), None)
                    if from_node_data and from_node_data.get("node_type") == "input":
                        param_name = conn.get("to_parameter")
                        if param_name and param_name not in [p["name"] for p in input_params]:
                            input_params.append({
                                'name': param_name,
                                'type': 'image',
                                'connectable': True
                            })
                if not input_params:
                    input_params.append({'name': 'image', 'type': 'image', 'connectable': True})
                new_node = CanvasNode(
                    node_data["name"],
                    node_data["category"],
                    node_data["position"][0],
                    node_data["position"][1],
                    tuple(node_data["color"]),
                    node_data["parameters"].copy(),
                    input_params,
                    node_type="algorithm"
                )
                new_node.pipeline_data = pipeline_data_embedded
                new_node.algorithm_outputs = node_data.get("algorithm_outputs", ["image"])
                new_node.update_connection_points()
                self.canvas.nodes.append(new_node)
                node_map[node_data["id"]] = new_node
            elif node_data.get("node_type") == "process":
                param_info = self._get_parameter_info(node_data["name"])
                new_node = CanvasNode(
                    node_data["name"],
                    node_data["category"],
                    node_data["position"][0],
                    node_data["position"][1],
                    tuple(node_data["color"]),
                    node_data["parameters"].copy(),
                    param_info,
                    node_type="process"
                )
                self.canvas.nodes.append(new_node)
                node_map[node_data["id"]] = new_node
        for conn_data in pipeline_data.get("connections", []):
            from_node = node_map.get(conn_data["from_node"])
            to_node = node_map.get(conn_data["to_node"])
            to_parameter = conn_data.get("to_parameter")
            from_output = conn_data.get("from_output", "image")
            if from_node and to_node:
                self.canvas.add_connection(from_node, to_node, to_parameter, from_output)
            else:
                if not from_node:
                    print(f"Warning: Could not find from_node for connection: {conn_data['from_node']}")
                if not to_node:
                    print(f"Warning: Could not find to_node for connection: {conn_data['to_node']}")
        return