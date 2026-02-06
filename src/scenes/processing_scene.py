from pygame import VIDEORESIZE, surfarray, image
from pathlib import Path
from json import load, dump
from datetime import datetime
from time import time, sleep
from enum import Enum
import numpy as np
from traceback import print_exc
from camera import CameraThread
from windows.file_viewer import FileViewer
from windows.menu_bar import MenuBar
from windows.node_canvas import NodeCanvas, CanvasNode, NodeType
from windows.processing_window import ProcessingViewport
from windows.processing_panel import ProcessingControlPanel
from windows.parameter_panel import ParameterPanel
from pipeline_execution import PipelineExecutor
from typing import List, Optional, Dict, Any

class ViewMode(Enum):
    """View modes for the viewport"""
    INPUT = "input"
    OUTPUT = "output"
    LIVE = "live"
    PIPELINE = "pipeline"

class ProcessingScene:
    """
    Scene for processing images through pipelines
    
    Features:
    - Select single image for processing
    - Select pipeline to apply
    - Process image and view output
    - Live view mode: process camera feed in real-time
    - Preview pipeline structure
    - Adjust parameters during live view
    - Export results with documentation
    """
    
    # Directory paths
    PIPELINES_DIR = "pipelines"
    WORKING_DIR = "working_directory"
    OUTPUT_DIR = "processed_outputs"
    NODE_DEFINITIONS_FILE = "nodes_definition.json"
    MIN_FRAME_TIME = 0.001
    
    def __init__(self, screen, settings, switch_scene_callback):
        """
        Initialize the Processing Scene
        
        Args:
            screen: Pygame display surface
            settings: Settings instance
            switch_scene_callback: Callback to switch between scenes
        """
        self.settings = settings
        self.switch_scene_callback = switch_scene_callback
        self.current_window_size = screen.get_size()
        
        # Camera reference
        self.camera_thread = None
        
        # Setup directories
        self._setup_directories()
        
        # Setup UI components
        self.setup_menu_bar()
        self.setup_file_viewer()
        self.setup_pipeline_viewer()
        self.setup_viewport()
        self.setup_control_panel()
        self.setup_parameter_panel()
        
        # Initial layout
        self.update_layout(*self.current_window_size)
        
        # State
        self.selected_image: Optional[Path] = None
        self.selected_pipeline: Optional[Path] = None
        self.output_image: Optional[Any] = None
        self.output_data: Optional[Dict[str, Any]] = None
        
        self.pipeline_executor: Optional[PipelineExecutor] = None
        
        # Live view state
        self.is_live_view_active = False
        self.last_frame_time = 0.0
        self.processing_fps = 0.0
        self.frame_count = 0
        self.fps_update_time = time()
    
    def _setup_directories(self):
        """Setup working directories"""
        self.pipeline_dir = Path.cwd() / self.PIPELINES_DIR
        self.working_dir = Path.cwd() / self.WORKING_DIR
        self.output_dir = Path.cwd() / self.OUTPUT_DIR
        
        for directory in [self.pipeline_dir, self.working_dir, self.output_dir]:
            if not directory.exists():
                directory.mkdir(parents=True)
                print(f"Created directory: {directory}")
        return
    
    def setup_menu_bar(self):
        """Setup the menu bar"""
        self.menu_bar = MenuBar(
            scene_instance=self,
            scene="processing",
            rel_pos=(0.0, 0.0),
            rel_size=(1.0, 0.05),
            switch_scene_callback=self.switch_scene_callback,
            call_methods=[self._save_output],
            reference_resolution=self.settings.saved_settings["display"]["resolution"]
        )
        return
    
    def setup_file_viewer(self):
        """Setup the image file viewer (left panel)"""
        self.file_viewer = FileViewer(
            rel_pos=(0.001, 0.051),
            rel_size=(0.248, 0.648),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            folder_color=(100, 150, 200),
            file_color=(200, 200, 200),
            selected_color=(80, 120, 160),
            hover_color=(60, 60, 80),
            text_color=(255, 255, 255)
        )
        self.file_viewer.allow_multi_select = False
        return
    
    def setup_pipeline_viewer(self):
        """Setup the pipeline file viewer (right panel)"""
        self.pipeline_viewer = FileViewer(
            rel_pos=(0.751, 0.051),
            rel_size=(0.248, 0.648),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            folder_color=(100, 150, 200),
            file_color=(200, 200, 200),
            selected_color=(80, 120, 160),
            hover_color=(60, 60, 80),
            text_color=(255, 255, 255)
        )
        self.pipeline_viewer.IMAGE_EXTENSIONS = {'.json'}
        self.pipeline_viewer.allow_multi_select = False
        return
    
    def setup_viewport(self):
        """Setup the processing viewport (center)"""
        self.viewport = ProcessingViewport(
            rel_pos=(0.251, 0.051),
            rel_size=(0.498, 0.648),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30)
        )
        return
    
    def setup_control_panel(self):
        """Setup the control panel (bottom center)"""
        self.control_panel = ProcessingControlPanel(
            rel_pos=(0.251, 0.701),
            rel_size=(0.498, 0.148),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            on_process_image=self.process_image,
            on_toggle_live_view=self.toggle_live_view,
            on_view_mode_change=self.set_view_mode
        )
        return
    
    def setup_parameter_panel(self):
        """Setup the parameter panel (bottom left)"""
        self.parameter_panel = ParameterPanel(
            rel_pos=(0.001, 0.701),
            rel_size=(0.248, 0.298),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            header_color=(60, 60, 60),
            text_color=(255, 255, 255),
            param_bg_color=(50, 50, 50)
        )
        return
    
    def update_layout(self, width: int, height: int):
        """
        Update all component layouts when window is resized
        
        Args:
            width: New window width
            height: New window height
        """
        self.current_window_size = (width, height)
        self.menu_bar.update_layout((width, height))
        self.file_viewer.update_layout((width, height))
        self.pipeline_viewer.update_layout((width, height))
        self.viewport.update_layout((width, height))
        self.control_panel.update_layout((width, height))
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
        self.menu_bar.handle_events(events)
        self.file_viewer.handle_events(events)
        self.pipeline_viewer.handle_events(events)
        self.viewport.handle_events(events)
        self.control_panel.handle_events(events)
        self.parameter_panel.handle_events(events)
        return
    
    def update(self):
        """Update scene state (called every frame)"""
        self.file_viewer.update()
        self.pipeline_viewer.update()
        self.viewport.update()
        self.control_panel.update()
        self.parameter_panel.update()
        self._update_selected_image()
        self._update_selected_pipeline()
        if self.is_live_view_active:
            self._update_live_view()
        return
    
    def draw(self, screen):
        """
        Draw the scene
        
        Args:
            screen: Pygame surface to draw on
        """
        self.menu_bar.draw(screen)
        self.file_viewer.draw(screen)
        self.pipeline_viewer.draw(screen)
        self.viewport.draw(screen)
        self.control_panel.draw(screen)
        self.parameter_panel.draw(screen)
        return
    
    def on_scene_enter(self):
        """Called when scene becomes active"""
        self.file_viewer.load_directory(str(self.working_dir))
        self.pipeline_viewer.load_directory(str(self.pipeline_dir))
        self._get_camera_reference()
        return
    
    def cleanup(self):
        """Cleanup scene resources"""
        if self.is_live_view_active:
            self.stop_live_view()
        return
    
    def _get_camera_reference(self):
        """Get camera reference from image acquisition scene"""
        try:
            if hasattr(self, 'switch_scene_callback'):
                pass
        except Exception as e:
            print(f"Note: Camera will be accessed when starting live view: {e}")
        return
    
    def _access_camera(self):
        """
        Access the camera from ImageAcquisitionScene
        
        Returns:
            Camera thread instance or None
        """
        if self.camera_thread is None:
            try:
                self.camera_thread = CameraThread()
                if not self.camera_thread.start():
                    print(f"Failed to start camera: {self.camera_thread.last_error}")
                    self.camera_thread = None
                    return None
            except Exception as e:
                print(f"Error creating camera: {e}")
                return None
        return self.camera_thread
    
    def _update_selected_image(self):
        """Update selected image from file viewer"""
        current_selection = self.file_viewer.get_selected_files()
        new_image = current_selection[0] if current_selection else None
        if new_image != self.selected_image:
            self.selected_image = new_image
            if self.selected_image:
                self._load_input_image()
                self.control_panel.set_image_selected(True)
            else:
                self.control_panel.set_image_selected(False)
        return
    
    def _update_selected_pipeline(self):
        """Update selected pipeline from pipeline viewer"""
        current_selection = self.pipeline_viewer.get_selected_files()
        new_pipeline = current_selection[0] if current_selection else None
        if new_pipeline != self.selected_pipeline:
            self.selected_pipeline = new_pipeline
            
            if self.selected_pipeline:
                self._load_pipeline()
                self.control_panel.set_pipeline_selected(True)
            else:
                self.viewport.set_pipeline_canvas(None)
                self.pipeline_executor = None
                self.control_panel.set_pipeline_selected(False)
                self.parameter_panel.clear_selection()
        return
    
    def set_view_mode(self, mode: str):
        """
        Switch viewport display mode
        
        Args:
            mode: View mode ('input', 'output', 'live', 'pipeline')
        """
        try:
            view_mode = ViewMode(mode)
            self.viewport.set_view_mode(view_mode.value)
        except ValueError:
            print(f"Invalid view mode: {mode}")
        return
    
    def _load_input_image(self):
        """Load selected input image for preview"""
        if not self.selected_image:
            return
        try:
            img = image.load(str(self.selected_image))
            self.viewport.set_input_image(img)
            self.set_view_mode(ViewMode.INPUT.value)
            print(f"Loaded image: {self.selected_image.name}")
        except Exception as e:
            print(f"Error loading {self.selected_image}: {e}")
        return
    
    def _load_pipeline(self):
        """Load selected pipeline and create executor"""
        if not self.selected_pipeline:
            return
        try:
            with open(self.selected_pipeline, 'r') as f:
                pipeline_data = load(f)
            self.pipeline_executor = PipelineExecutor(pipeline_data)
            node_definitions = self._load_node_definitions()
            canvas = self._create_pipeline_canvas(node_definitions)
            self._deserialize_pipeline_to_canvas(pipeline_data, canvas)
            self.viewport.set_pipeline_canvas(canvas)
            self._update_parameter_panel_for_first_node(canvas)
            print(f"Loaded pipeline: {self.selected_pipeline.name}")
        except Exception as e:
            print(f"Error loading pipeline: {e}")
            print_exc()
        return
    
    def _load_node_definitions(self) -> Dict[str, Any]:
        """
        Load node definitions from JSON file
        
        Returns:
            Dictionary with node definitions or empty structure
        """
        node_defs_path = Path(self.NODE_DEFINITIONS_FILE)
        if node_defs_path.exists():
            try:
                with open(node_defs_path, 'r') as f:
                    return load(f)
            except Exception as e:
                print(f"Error loading node definitions: {e}")
        return {"categories": []}
    
    def _create_pipeline_canvas(self, node_definitions: Dict[str, Any]) -> NodeCanvas:
        """
        Create a new NodeCanvas for displaying pipeline
        
        Args:
            node_definitions: Node type definitions
            
        Returns:
            Configured NodeCanvas instance
        """
        canvas = NodeCanvas(
            rel_pos=(0.251, 0.051),
            rel_size=(0.498, 0.648),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            grid_color=(50, 50, 50),
            text_color=(255, 255, 255),
            selection_color=(255, 200, 0),
            connection_color=(150, 150, 150),
            node_definitions=node_definitions
        )
        canvas.update_layout(self.current_window_size)
        return canvas
    
    def _deserialize_pipeline_to_canvas(self, pipeline_data: Dict[str, Any], canvas: NodeCanvas):
        """
        Deserialize pipeline data into canvas nodes and connections
        
        Args:
            pipeline_data: Serialized pipeline dictionary
            canvas: Canvas to populate
        """
        node_map = {}
        self._map_io_nodes(pipeline_data, canvas, node_map)
        self._create_process_nodes(pipeline_data, canvas, node_map)
        self._create_connections(pipeline_data, canvas, node_map)
        return
    
    def _map_io_nodes(self, pipeline_data: Dict[str, Any], 
                      canvas: NodeCanvas, node_map: Dict[str, CanvasNode]):
        """Map existing input/output nodes to pipeline node IDs"""
        for node in canvas.nodes:
            if node.node_type == NodeType.INPUT:
                for node_data in pipeline_data.get("nodes", []):
                    if node_data.get("node_type") == "input":
                        node.rect.x = node_data["position"][0]
                        node.rect.y = node_data["position"][1]
                        node.update_connection_points()
                        node_map[node_data["id"]] = node
                        break
            elif node.node_type == NodeType.OUTPUT:
                for node_data in pipeline_data.get("nodes", []):
                    if node_data.get("node_type") == "output":
                        node.rect.x = node_data["position"][0]
                        node.rect.y = node_data["position"][1]
                        node.update_connection_points()
                        node_map[node_data["id"]] = node
                        break
        return
    
    def _create_process_nodes(self, pipeline_data: Dict[str, Any], 
                              canvas: NodeCanvas, node_map: Dict[str, CanvasNode]):
        """Create process nodes from pipeline data"""
        for node_data in pipeline_data.get("nodes", []):
            if node_data.get("node_type") in ["input", "output"]:
                continue
            new_node = CanvasNode(
                node_data["name"],
                node_data.get("category", ""),
                node_data["position"][0],
                node_data["position"][1],
                tuple(node_data["color"]),
                node_data["parameters"].copy(),
                [],
                node_type="process"
            )
            canvas.nodes.append(new_node)
            node_map[node_data["id"]] = new_node
        return
    
    def _create_connections(self, pipeline_data: Dict[str, Any], 
                           canvas: NodeCanvas, node_map: Dict[str, CanvasNode]):
        """Create connections between nodes"""
        for conn_data in pipeline_data.get("connections", []):
            from_node = node_map.get(conn_data["from_node"])
            to_node = node_map.get(conn_data["to_node"])
            to_param = conn_data.get("to_parameter")
            from_output = conn_data.get("from_output", "image")
            if from_node and to_node:
                canvas.add_connection(from_node, to_node, to_param, from_output)
        return
    
    def _update_parameter_panel_for_first_node(self, canvas: NodeCanvas):
        """
        Update parameter panel with the first process node's parameters
        
        Args:
            canvas: Canvas containing nodes
        """
        for node in canvas.nodes:
            if node.node_type == NodeType.PROCESS:
                params = self._get_parameter_definitions(node.name)
                for param in params:
                    param_name = param['name']
                    if param_name in node.parameters:
                        param['value'] = node.parameters[param_name]
                
                self.parameter_panel.set_selected_node(node, node.name, params)
                break
        return
    
    def _get_parameter_definitions(self, node_name: str) -> List[Dict[str, Any]]:
        """
        Get parameter definitions for a node type from JSON
        
        Args:
            node_name: Name of the node type
            
        Returns:
            List of parameter definition dictionaries
        """
        node_defs = self._load_node_definitions()
        for category in node_defs.get('categories', []):
            for node in category.get('nodes', []):
                if node['name'] == node_name:
                    return node.get('parameters', [])
        return []
    
    def _update_live_view(self):
        """Update live view processing (called every frame)"""
        if not self.camera_thread or not self.camera_thread.is_running:
            print("Camera stopped, ending live view")
            self.stop_live_view()
            return
        frame_surface = self.camera_thread.get_frame()
        if frame_surface is None:
            return
        try:
            start_time = time()
            result = self.pipeline_executor.execute(frame_surface)
            if isinstance(result, dict):
                output_array = result.get("image")
                if output_array is not None:
                    if len(output_array.shape) == 3:
                        output_array = np.transpose(output_array, (1, 0, 2))
                        output_surface = surfarray.make_surface(output_array)
                    else:
                        rgb_array = np.stack([output_array] * 3, axis=-1)
                        rgb_array = np.transpose(rgb_array, (1, 0, 2))
                        output_surface = surfarray.make_surface(rgb_array)
                    self.viewport.set_live_frame(output_surface)
            elif isinstance(result, np.ndarray):
                if len(result.shape) == 3:
                    output_array = np.transpose(result, (1, 0, 2))
                    output_surface = surfarray.make_surface(output_array)
                else:
                    rgb_array = np.stack([result] * 3, axis=-1)
                    rgb_array = np.transpose(rgb_array, (1, 0, 2))
                    output_surface = surfarray.make_surface(rgb_array)
                self.viewport.set_live_frame(output_surface)
            else:
                self.viewport.set_live_frame(result)
            process_time = time() - start_time
            self.frame_count += 1
            current_time = time()
            if current_time - self.fps_update_time >= 1.0:
                self.processing_fps = self.frame_count / (current_time - self.fps_update_time)
                self.control_panel.set_processing_fps(self.processing_fps, process_time)
                self.frame_count = 0
                self.fps_update_time = current_time
            sleep_time = max(0, self.MIN_FRAME_TIME - process_time)
            if sleep_time > 0:
                sleep(sleep_time)
            self.last_frame_time = current_time
        except Exception as e:
            print(f"Error in live view processing: {e}")
            print_exc()
        return
    
    def toggle_live_view(self):
        """Toggle live view processing on/off"""
        if self.is_live_view_active:
            self.stop_live_view()
        else:
            self.start_live_view()
        return
    
    def start_live_view(self):
        """Start live view processing"""
        if not self.pipeline_executor:
            print("No pipeline selected")
            return
        camera = self._access_camera()
        if not camera or not camera.is_running:
            print("Camera not available")
            return
        self.is_live_view_active = True
        self.frame_count = 0
        self.fps_update_time = time()
        self.set_view_mode(ViewMode.LIVE.value)
        self.control_panel.set_live_view_active(True)
        print("Live view started")
        return
    
    def stop_live_view(self):
        """Stop live view processing"""
        self.is_live_view_active = False
        self.control_panel.set_live_view_active(False)
        print(f"Live view stopped (avg FPS: {self.processing_fps:.1f})")
        return
    
    def _update_live_view(self):
        """Update live view processing (called every frame)"""
        if not self.camera_thread or not self.camera_thread.is_running:
            print("Camera stopped, ending live view")
            self.stop_live_view()
            return
        frame_surface = self.camera_thread.get_frame()
        if frame_surface is None:
            return
        try:
            start_time = time()
            result = self.pipeline_executor.execute(frame_surface)
            if isinstance(result, dict):
                output_array = result.get("image")
                if output_array is not None:
                    if len(output_array.shape) == 3:
                        output_array = np.transpose(output_array, (1, 0, 2))
                        output_surface = surfarray.make_surface(output_array)
                    else:
                        rgb_array = np.stack([output_array] * 3, axis=-1)
                        rgb_array = np.transpose(rgb_array, (1, 0, 2))
                        output_surface = surfarray.make_surface(rgb_array)
                    self.viewport.set_live_frame(output_surface)
            elif isinstance(result, np.ndarray):
                if len(result.shape) == 3:
                    output_array = np.transpose(result, (1, 0, 2))
                    output_surface = surfarray.make_surface(output_array)
                else:
                    rgb_array = np.stack([result] * 3, axis=-1)
                    rgb_array = np.transpose(rgb_array, (1, 0, 2))
                    output_surface = surfarray.make_surface(rgb_array)
                self.viewport.set_live_frame(output_surface)
            else:
                self.viewport.set_live_frame(result)
            process_time = time() - start_time
            self.frame_count += 1
            current_time = time()
            if current_time - self.fps_update_time >= 1.0:
                self.processing_fps = self.frame_count / (current_time - self.fps_update_time)
                self.control_panel.set_processing_fps(self.processing_fps, process_time)
                self.frame_count = 0
                self.fps_update_time = current_time
            sleep_time = max(0, self.MIN_FRAME_TIME - process_time)
            if sleep_time > 0:
                sleep(sleep_time)
            self.last_frame_time = current_time
        except Exception as e:
            print(f"Error in live view processing: {e}")
            print_exc()
        return
    
    def _save_output(self):
        """Save processed output (menu callback)"""
        if not self.output_image:
            print("No output to save")
            return
        try:
            from tkinter import Tk, filedialog
            root = Tk()
            root.withdraw()
            filepath = filedialog.asksaveasfilename(
                title="Save Output Image",
                defaultextension=".png",
                filetypes=[
                    ("PNG files", "*.png"),
                    ("JPEG files", "*.jpg"),
                    ("All files", "*.*")
                ],
                initialdir=str(self.output_dir) if self.output_dir.exists() else None
            )
            root.destroy()
            if not filepath:
                return
            image.save(self.output_image, filepath)
            print(f"Output saved to: {filepath}")
            if self.output_data:
                metadata_path = Path(filepath).with_suffix('.json')
                with open(metadata_path, 'w') as f:
                    dump({
                        "processing_date": datetime.now().isoformat(),
                        "input_image": str(self.selected_image.name) if self.selected_image else "None",
                        "pipeline": str(self.selected_pipeline.name) if self.selected_pipeline else "None",
                        "data": self.output_data
                    }, f, indent=2)
                print(f"Metadata saved to: {metadata_path}")
        except Exception as e:
            print(f"Error saving output: {e}")
            print_exc()
        return