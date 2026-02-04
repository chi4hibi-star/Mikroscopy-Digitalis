from pygame import VIDEORESIZE, surfarray, image
from pathlib import Path
from json import load, dump
from datetime import datetime
from threading import Thread
from queue import Queue, Empty
from enum import Enum
from dataclasses import dataclass
import numpy as np
from traceback import print_exc
from shutil import copy2
from windows.file_viewer import FileViewer
from windows.menu_bar import MenuBar
from windows.node_canvas import NodeCanvas, CanvasNode, NodeType
from windows.processing_window import ProcessingViewport
from windows.processing_panel import ProcessingControlPanel
from pipeline_execution import PipelineExecutor
from typing import Tuple, List, Optional, Dict, Any

class ProcessingMessageType(Enum):
    """Types of messages from processing thread"""
    PROGRESS = "progress"
    COMPLETE = "complete"
    ERROR = "error"

@dataclass
class ProcessingMessage:
    """Message from processing thread to main thread"""
    message_type: ProcessingMessageType
    current: int = 0
    total: int = 0
    outputs: Optional[List[Any]] = None
    data_outputs: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None

class ProcessingScene:
    """
    Scene for batch processing images through pipelines
    
    Features:
    - Select multiple images from file viewer
    - Select pipeline to apply
    - Preview pipeline structure
    - Process images in background thread
    - View input/output/pipeline
    - Export results with documentation
    """
    
    # Directory paths
    PIPELINES_DIR = "pipelines"
    WORKING_DIR = "working_directory"
    OUTPUT_DIR = "processed_outputs"
    NODE_DEFINITIONS_FILE = "nodes_definition.json"
    
    # Queue polling
    QUEUE_POLL_TIMEOUT = 0.01
    
    # Thread timeout
    THREAD_JOIN_TIMEOUT = 1.0
    
    # File extensions
    PIPELINE_EXTENSION = '.json'
    OUTPUT_IMAGE_FORMAT = 'output_{:04d}.png'
    
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
        
        # Setup directories
        self._setup_directories()
        
        # Setup UI components
        self.setup_menu_bar()
        self.setup_file_viewer()
        self.setup_pipeline_viewer()
        self.setup_viewport()
        self.setup_control_panel()
        
        # Initial layout
        self.update_layout(*self.current_window_size)
        
        # State
        self.selected_images: List[Path] = []
        self.selected_pipeline: Optional[Path] = None
        self.output_images: List[Any] = []
        self.output_data: List[Dict[str, Any]] = []
        
        # Processing thread
        self.processing_thread: Optional[Thread] = None
        self.processing_queue: Queue = Queue()
    
    # ==================== Setup Methods ====================
    
    def _setup_directories(self):
        """Setup working directories"""
        self.pipeline_dir = Path.cwd() / self.PIPELINES_DIR
        self.working_dir = Path.cwd() / self.WORKING_DIR
        self.output_dir = Path.cwd() / self.OUTPUT_DIR
        
        for directory in [self.pipeline_dir, self.working_dir, self.output_dir]:
            if not directory.exists():
                directory.mkdir(parents=True)
                print(f"Created directory: {directory}")
    
    def setup_menu_bar(self):
        """Setup the menu bar"""
        self.menu_bar = MenuBar(
            scene_instance=self,
            scene="processing",
            rel_pos=(0.0, 0.0),
            rel_size=(1.0, 0.05),
            switch_scene_callback=self.switch_scene_callback,
            call_methods=[self._load_images, self._save_output],
            reference_resolution=self.settings.saved_settings["display"]["resolution"]
        )
    
    def setup_file_viewer(self):
        """Setup the image file viewer (left panel)"""
        self.file_viewer = FileViewer(
            rel_pos=(0.001, 0.051),
            rel_size=(0.248, 0.948),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            folder_color=(100, 150, 200),
            file_color=(200, 200, 200),
            selected_color=(80, 120, 160),
            hover_color=(60, 60, 80),
            text_color=(255, 255, 255)
        )
    
    def setup_pipeline_viewer(self):
        """Setup the pipeline file viewer (right panel)"""
        self.pipeline_viewer = FileViewer(
            rel_pos=(0.751, 0.051),
            rel_size=(0.248, 0.948),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30),
            folder_color=(100, 150, 200),
            file_color=(200, 200, 200),
            selected_color=(80, 120, 160),
            hover_color=(60, 60, 80),
            text_color=(255, 255, 255)
        )
        # Only show JSON files in pipeline viewer
        self.pipeline_viewer.IMAGE_EXTENSIONS = {self.PIPELINE_EXTENSION}
    
    def setup_viewport(self):
        """Setup the processing viewport (center)"""
        self.viewport = ProcessingViewport(
            rel_pos=(0.251, 0.051),
            rel_size=(0.498, 0.608),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            background_color=(30, 30, 30)
        )
    
    def setup_control_panel(self):
        """Setup the control panel (bottom center)"""
        self.control_panel = ProcessingControlPanel(
            rel_pos=(0.251, 0.661),
            rel_size=(0.498, 0.208),
            reference_resolution=self.settings.saved_settings["display"]["resolution"],
            settings=self.settings,
            on_process=self.process_images,
            on_output_mode_change=self._save_output_mode,
            on_set_view_mode=self.set_view_mode
        )
    
    # ==================== Scene Lifecycle ====================
    
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
    
    def handle_events(self, events: list):
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout(event.w, event.h)
        
        # Pass events to all components
        self.menu_bar.handle_events(events)
        self.file_viewer.handle_events(events)
        self.pipeline_viewer.handle_events(events)
        self.viewport.handle_events(events)
        self.control_panel.handle_events(events)
    
    def update(self):
        """Update scene state (called every frame)"""
        # Update all components
        self.file_viewer.update()
        self.pipeline_viewer.update()
        self.viewport.update()
        self.control_panel.update()
        
        # Handle image selection changes
        self._update_selected_images()
        
        # Handle pipeline selection changes
        self._update_selected_pipeline()
        
        # Process messages from processing thread
        self._process_queue_messages()
    
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
    
    def on_scene_enter(self):
        """Called when scene becomes active"""
        self.file_viewer.load_directory(str(self.working_dir))
        self.pipeline_viewer.load_directory(str(self.pipeline_dir))
    
    def cleanup(self):
        """Cleanup scene resources"""
        if self.processing_thread and self.processing_thread.is_alive():
            print("Waiting for processing thread to finish...")
            self.processing_thread.join(timeout=self.THREAD_JOIN_TIMEOUT)
            if self.processing_thread.is_alive():
                print("Warning: Processing thread did not finish in time")
    
    # ==================== State Management ====================
    
    def _update_selected_images(self):
        """Update selected images from file viewer"""
        current_images = self.file_viewer.get_selected_files()
        if current_images != self.selected_images:
            self.selected_images = current_images
            self.control_panel.set_image_count(len(current_images))
            self._load_input_images()
    
    def _update_selected_pipeline(self):
        """Update selected pipeline from pipeline viewer"""
        current_pipeline = self.pipeline_viewer.get_selected_files()
        
        # Pipeline deselected
        if len(current_pipeline) == 0 and self.selected_pipeline is not None:
            self.selected_pipeline = None
            self.viewport.set_pipeline_canvas(None)
        
        # Pipeline selected or changed
        elif len(current_pipeline) > 0:
            if self.selected_pipeline != current_pipeline[0]:
                self.selected_pipeline = current_pipeline[0]
                self._load_pipeline()
    
    def _process_queue_messages(self):
        """Process messages from the processing thread"""
        try:
            while True:
                msg_dict = self.processing_queue.get_nowait()
                msg = self._parse_queue_message(msg_dict)
                
                if msg.message_type == ProcessingMessageType.PROGRESS:
                    self.control_panel.set_processing(True, msg.current, msg.total)
                
                elif msg.message_type == ProcessingMessageType.COMPLETE:
                    self.control_panel.set_processing(False)
                    self.output_images = msg.outputs or []
                    self.output_data = msg.data_outputs or []
                    self._display_outputs()
                
                elif msg.message_type == ProcessingMessageType.ERROR:
                    self.control_panel.set_processing(False)
                    print(f"Processing error: {msg.error}")
        except Empty:
            pass
    
    def _parse_queue_message(self, msg_dict: Dict[str, Any]) -> ProcessingMessage:
        """
        Parse queue message dictionary into ProcessingMessage
        
        Args:
            msg_dict: Dictionary from queue
            
        Returns:
            Parsed ProcessingMessage
        """
        msg_type_str = msg_dict.get("type", "unknown")
        try:
            msg_type = ProcessingMessageType(msg_type_str)
        except ValueError:
            msg_type = ProcessingMessageType.ERROR
        
        return ProcessingMessage(
            message_type=msg_type,
            current=msg_dict.get("current", 0),
            total=msg_dict.get("total", 0),
            outputs=msg_dict.get("outputs"),
            data_outputs=msg_dict.get("data_outputs"),
            error=msg_dict.get("error")
        )
    
    def set_view_mode(self, mode: str):
        """
        Switch viewport display mode
        
        Args:
            mode: View mode ('input', 'output', 'pipeline')
        """
        self.viewport.current_mode = mode
    
    # ==================== Image Loading ====================
    
    def _load_input_images(self):
        """Load selected input images for preview"""
        images = []
        for img_path in self.selected_images:
            try:
                img = image.load(str(img_path))
                images.append(img)
            except Exception as e:
                print(f"Error loading {img_path}: {e}")
        
        self.viewport.set_input_images(images)
    
    def _load_images(self):
        """Load images from file system (menu callback)"""
        try:
            from tkinter import Tk, filedialog
            root = Tk()
            root.withdraw()
            
            filepaths = filedialog.askopenfilenames(
                title="Select Images to Process",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                    ("All files", "*.*")
                ],
                initialdir=str(self.working_dir) if self.working_dir.exists() else None
            )
            root.destroy()
            
            if not filepaths:
                return
            
            # Copy to working directory
            if not self.working_dir.exists():
                self.working_dir.mkdir(parents=True)
            
            count = 0
            for filepath in filepaths:
                source_file = Path(filepath)
                destination = self.working_dir / source_file.name
                copy2(source_file, destination)
                count += 1
            
            if count > 0:
                print(f"Loaded {count} images")
                self.file_viewer.load_directory(str(self.working_dir))
        except Exception as e:
            print(f"Error loading images: {e}")
            print_exc()
    
    # ==================== Pipeline Loading ====================
    
    def _load_pipeline(self):
        """Load selected pipeline and display in viewport"""
        if not self.selected_pipeline:
            return
        
        try:
            # Load pipeline data
            with open(self.selected_pipeline, 'r') as f:
                pipeline_data = load(f)
            
            # Load node definitions
            node_definitions = self._load_node_definitions()
            
            # Create canvas and deserialize pipeline
            canvas = self._create_pipeline_canvas(node_definitions)
            self._deserialize_pipeline_to_canvas(pipeline_data, canvas)
            
            # Display in viewport
            self.viewport.set_pipeline_canvas(canvas)
            self.set_view_mode("pipeline")
            
            print(f"Loaded pipeline: {self.selected_pipeline.name}")
        except Exception as e:
            print(f"Error loading pipeline: {e}")
            print_exc()
    
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
        
        # Map existing input/output nodes
        self._map_io_nodes(pipeline_data, canvas, node_map)
        
        # Create process nodes
        self._create_process_nodes(pipeline_data, canvas, node_map)
        
        # Create connections
        self._create_connections(pipeline_data, canvas, node_map)
        return
    
    def _map_io_nodes(self, pipeline_data: Dict[str, Any], 
                      canvas: NodeCanvas, node_map: Dict[str, CanvasNode]):
        """
        Map existing input/output nodes to pipeline node IDs
        
        Args:
            pipeline_data: Serialized pipeline dictionary
            canvas: Canvas containing default I/O nodes
            node_map: Dictionary to populate with node mappings
        """
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
        """
        Create process nodes from pipeline data
        
        Args:
            pipeline_data: Serialized pipeline dictionary
            canvas: Canvas to add nodes to
            node_map: Dictionary to populate with node mappings
        """
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
        """
        Create connections between nodes
        
        Args:
            pipeline_data: Serialized pipeline dictionary
            canvas: Canvas to add connections to
            node_map: Dictionary mapping node IDs to CanvasNode instances
        """
        for conn_data in pipeline_data.get("connections", []):
            from_node = node_map.get(conn_data["from_node"])
            to_node = node_map.get(conn_data["to_node"])
            to_param = conn_data.get("to_parameter")
            from_output = conn_data.get("from_output", "image")
            if from_node and to_node:
                canvas.add_connection(from_node, to_node, to_param, from_output)
            else:
                if not from_node:
                    print(f"Warning: Could not find from_node: {conn_data['from_node']}")
                if not to_node:
                    print(f"Warning: Could not find to_node: {conn_data['to_node']}")
        return
    
    def process_images(self):
        """Process selected images through the selected pipeline"""
        if not self.selected_images:
            print("No images selected")
            return
        if not self.selected_pipeline:
            print("No pipeline selected")
            return
        try:
            with open(self.selected_pipeline, 'r') as f:
                pipeline_data = load(f)
        except Exception as e:
            print(f"Error loading pipeline: {e}")
            return
        self.control_panel.set_processing(True, 0, len(self.selected_images))
        self.processing_thread = Thread(
            target=self._process_images_thread,
            args=(self.selected_images, pipeline_data),
            daemon=True
        )
        self.processing_thread.start()
        print(f"Started processing {len(self.selected_images)} images...")
        return
    
    def _process_images_thread(self, image_paths: List[Path], pipeline_data: Dict[str, Any]):
        """
        Process images in a separate thread (background processing)
        
        Args:
            image_paths: List of image file paths to process
            pipeline_data: Pipeline configuration dictionary
        """
        executor = PipelineExecutor(pipeline_data)
        outputs = []
        data_outputs = []
        for i, img_path in enumerate(image_paths):
            try:
                img_surface = image.load(str(img_path))
                img_array = surfarray.array3d(img_surface)
                img_array = np.transpose(img_array, (1, 0, 2))
                result = executor.execute(img_array)
                if isinstance(result, dict):
                    output_array = result.get("image")
                    data_output = result.get("data")
                else:
                    output_array = result
                    data_output = None
                if output_array is not None:
                    output_array = np.transpose(output_array, (1, 0, 2))
                    output_surface = surfarray.make_surface(output_array)
                    outputs.append(output_surface)
                else:
                    outputs.append(None)
                data_outputs.append({
                    "image_name": img_path.name,
                    "image_index": i,
                    "data": data_output
                })
                self.processing_queue.put({
                    "type": ProcessingMessageType.PROGRESS.value,
                    "current": i + 1,
                    "total": len(image_paths)
                })
            except Exception as e:
                print(f"Error processing {img_path}: {e}")
                print_exc()
                outputs.append(None)
                data_outputs.append({
                    "image_name": img_path.name,
                    "image_index": i,
                    "data": None
                })
        self.processing_queue.put({
            "type": ProcessingMessageType.COMPLETE.value,
            "outputs": outputs,
            "data_outputs": data_outputs
        })
        return
    
    def _display_outputs(self):
        """Display processed outputs in viewport"""
        self.viewport.set_output_images(self.output_images)
        self.set_view_mode("output")
        print(f"Processing complete: {len(self.output_images)} images")
        return
    
    def _save_output_mode(self, mode: str):
        """
        Save output mode preference to settings
        
        Args:
            mode: Output mode string
        """
        self.settings.saved_settings["processing"]["output_mode"] = mode
        with open("settings.json", "w") as f:
            dump(self.settings.saved_settings, f, indent=4)
        return
    
    def _save_output(self):
        """Save processed outputs (menu callback)"""
        if not self.output_images:
            print("No outputs to save")
            return
        try:
            from tkinter import Tk, filedialog
            root = Tk()
            root.withdraw()
            save_dir = filedialog.askdirectory(
                title="Select Output Directory",
                initialdir=str(self.output_dir) if self.output_dir.exists() else None
            )
            root.destroy()
            if not save_dir:
                return
            self._save_documentation(Path(save_dir))
        except Exception as e:
            print(f"Error saving output: {e}")
            print_exc()
        return
    
    def _save_documentation(self, save_path: Path):
        """
        Save full documentation including inputs, outputs, and metadata
        
        Args:
            save_path: Base directory for documentation
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            doc_dir = save_path / f"processing_doc_{timestamp}"
            doc_dir.mkdir(exist_ok=True)
            input_dir = doc_dir / "inputs"
            input_dir.mkdir(exist_ok=True)
            for img_path in self.selected_images:
                copy2(img_path, input_dir / img_path.name)
            output_dir = doc_dir / "outputs"
            output_dir.mkdir(exist_ok=True)
            for i, img in enumerate(self.output_images):
                filename = self.OUTPUT_IMAGE_FORMAT.format(i)
                image.save(img, str(output_dir / filename))
            if self.selected_pipeline:
                copy2(self.selected_pipeline, doc_dir / "pipeline.json")
            metadata = {
                "processing_date": datetime.now().isoformat(),
                "num_inputs": len(self.selected_images),
                "num_outputs": len(self.output_images),
                "pipeline": self.selected_pipeline.name if self.selected_pipeline else "None",
                "output_mode": self.settings.saved_settings.get("processing", {}).get("output_mode"),
                "camera": self.settings.saved_settings.get("camera"),
                "settings": self.settings.saved_settings
            }
            with open(doc_dir / "metadata.json", 'w') as f:
                dump(metadata, f, indent=2)
            readme = self._generate_readme(timestamp)
            with open(doc_dir / "README.md", 'w') as f:
                f.write(readme)
            print(f"Full documentation saved to: {doc_dir}")
        except Exception as e:
            print(f"Error saving documentation: {e}")
            print_exc()
        return
    
    def _generate_readme(self, timestamp: str) -> str:
        """
        Generate README content for documentation
        
        Args:
            timestamp: Processing timestamp
            
        Returns:
            README markdown content
        """
        return f"""# Processing Documentation
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Processing Details
- Input Images: {len(self.selected_images)}
- Output Images: {len(self.output_images)}
- Pipeline: {self.selected_pipeline.name if self.selected_pipeline else 'None'}
- Camera: {self.settings.saved_settings.get('camera', {}).get('device', 'Unknown')}

## Directory Structure
- inputs/ : Original input images
- outputs/ : Processed output images
- pipeline.json : Processing pipeline used
- metadata.json : Complete processing metadata

## Output Mode
{self.settings.saved_settings.get('processing', {}).get('output_mode', 'Unknown')}
"""