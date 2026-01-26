from pygame import VIDEORESIZE, surfarray, image
from pathlib import Path
from json import load, dump
from datetime import datetime
from threading import Thread
from queue import Queue
import numpy as np
from traceback import print_exc
from shutil import copy2
from windows.file_viewer import FileViewer
from windows.menu_bar import MenuBar
from windows.node_canvas import NodeCanvas, CanvasNode
from windows.processing_window import ProcessingViewport
from windows.processing_panel import ProcessingControlPanel
from pipeline_execution import PipelineExecutor

class ProcessingScene():
    def __init__(self, screen, settings, switch_scene_callback):
        self.settings = settings
        self.switch_scene_callback = switch_scene_callback
        window_width, window_height = screen.get_size()
        self.current_window_size = (window_width, window_height)
        self.setup_menu_bar()
        self.setup_file_viewer()
        self.setup_pipeline_viewer()
        self.setup_viewport()
        self.setup_control_panel()
        self.update_layout(window_width, window_height)
        self.selected_images = []
        self.selected_pipeline = None
        self.output_images = []
        self.output_data = []
        self.processing_thread = None
        self.processing_queue = Queue()
        self.pipeline_dir = Path.cwd() / "pipelines"
        if not self.pipeline_dir.exists():
            self.pipeline_dir.mkdir(parents=True)
        self.working_dir = Path.cwd() / "working_directory"
        if not self.working_dir.exists():
            self.working_dir.mkdir(parents=True)
        self.output_dir = Path.cwd() / "processed_outputs"
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)
        return
    
    def setup_menu_bar(self):
        """Setup the menu bar"""
        self.menu_bar = MenuBar(
            scene_instance=self,
            scene="processing",
            rel_pos=(0.0, 0.0),
            rel_size=(1.0, 0.05),
            switch_scene_callback=self.switch_scene_callback,
            reference_resolution=self.settings.saved_settings["resolution"]
        )
        return
    
    def setup_file_viewer(self):
        """Setup the image file viewer"""
        self.file_viewer = FileViewer(
            rel_pos=(0.001, 0.051),
            rel_size=(0.248, 0.948),
            reference_resolution=self.settings.saved_settings["resolution"],
            background_color=self.settings.saved_settings.get("backgroundcolor", [30, 30, 30]),
            folder_color=(100, 150, 200),
            file_color=(200, 200, 200),
            selected_color=(80, 120, 160),
            hover_color=(60, 60, 80),
            text_color=(255, 255, 255)
        )
        return
    
    def setup_pipeline_viewer(self):
        """Setup the pipeline file viewer"""
        self.pipeline_viewer = FileViewer(
            rel_pos=(0.751, 0.051),
            rel_size=(0.248, 0.948),
            reference_resolution=self.settings.saved_settings["resolution"],
            background_color=self.settings.saved_settings.get("backgroundcolor", [30, 30, 30]),
            folder_color=(100, 150, 200),
            file_color=(200, 200, 200),
            selected_color=(80, 120, 160),
            hover_color=(60, 60, 80),
            text_color=(255, 255, 255)
        )
        self.pipeline_viewer.image_extensions = {'.json'}
        return
    
    def setup_viewport(self):
        """Setup the processing viewport"""
        self.viewport = ProcessingViewport(
            rel_pos=(0.251, 0.051),
            rel_size=(0.498, 0.608),
            reference_resolution=self.settings.saved_settings["resolution"],
            background_color=self.settings.saved_settings.get("backgroundcolor", [30, 30, 30])
        )
        return
    
    def setup_control_panel(self):
        """Setup the control panel"""
        self.control_panel = ProcessingControlPanel(
            rel_pos=(0.251, 0.661),
            rel_size=(0.498, 0.208),
            reference_resolution=self.settings.saved_settings["resolution"],
            settings=self.settings,
            on_process=self.process_images,
            on_output_mode_change=self.save_output_mode,
            on_set_view_mode=self.set_view_mode
        )
        return
    
    def update_layout(self, width, height):
        """Update all component layouts"""
        self.current_window_size = (width, height)
        self.menu_bar.update_layout((width, height))
        self.file_viewer.update_layout((width, height))
        self.pipeline_viewer.update_layout((width, height))
        self.viewport.update_layout((width, height))
        self.control_panel.update_layout((width, height))
        return
    
    def handle_events(self, events):
        """Handle pygame events"""
        for event in events:
            if event.type == VIDEORESIZE:
                self.update_layout(event.w, event.h)
        self.menu_bar.handle_events(events)
        self.file_viewer.handle_events(events)
        self.pipeline_viewer.handle_events(events)
        self.viewport.handle_events(events)
        self.control_panel.handle_events(events)
        return
    
    def update(self):
        """Update scene state"""
        self.file_viewer.update()
        self.pipeline_viewer.update()
        self.viewport.update()
        self.control_panel.update()
        current_images = self.file_viewer.get_selected_files()
        if current_images != self.selected_images:
            self.selected_images = current_images
            self.control_panel.set_image_count(len(current_images))
            self._load_input_images()
        current_pipeline = self.pipeline_viewer.get_selected_files()
        if len(current_pipeline) == 0 and self.selected_pipeline is not None:
            self.selected_pipeline = None
            self.viewport.set_pipeline_canvas(None)
        elif len(current_pipeline) > 0:
            if self.selected_pipeline != current_pipeline[0]:
                self.selected_pipeline = current_pipeline[0]
                self._load_pipeline()
        if not self.processing_queue.empty():
            msg = self.processing_queue.get()
            if msg["type"] == "progress":
                self.control_panel.set_processing(True, msg["current"], msg["total"])
            elif msg["type"] == "complete":
                self.control_panel.set_processing(False)
                self.output_images = msg["outputs"]
                self.output_data = msg.get("data_outputs", [])
                self._display_outputs()
        return
    
    def draw(self, screen):
        """Draw the scene"""
        self.menu_bar.draw(screen)
        self.file_viewer.draw(screen)
        self.pipeline_viewer.draw(screen)
        self.viewport.draw(screen)
        self.control_panel.draw(screen)
        return
    
    def set_view_mode(self, mode):
        """Switch viewport mode"""
        self.viewport.current_mode = mode
        return
    
    def on_scene_enter(self):
        """Called when scene becomes active"""
        self.file_viewer.load_directory(str(self.working_dir))
        self.pipeline_viewer.load_directory(str(self.pipeline_dir))
        return
    
    def switch_scene(self, call):
        """Switch to a different scene"""
        self.switch_scene_callback(call)
        return
    
    def load_images(self):
        """Load images from a selected directory"""
        try:
            from tkinter import Tk, filedialog
            root = Tk()
            root.withdraw()
            directory = filedialog.askdirectory(title="Select Image Directory")
            root.destroy()
            if directory:
                self.file_viewer.load_directory(directory)
                print(f"Loaded images from: {directory}")
        except Exception as e:
            print(f"Error loading images: {e}")
        return
    
    def save_output_mode(self, mode):
        """Save output mode to settings"""
        self.settings.saved_settings["output_mode"] = mode
        with open("settings.json", "w") as f:
            dump(self.settings.saved_settings, f, indent=4)
        return
    
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
        return
    
    def _load_pipeline(self):
        """Load selected pipeline"""
        if not self.selected_pipeline:
            return
        try:
            with open(self.selected_pipeline, 'r') as f:
                pipeline_data = load(f)
            node_defs_path = Path("Nodes_definition.json")
            if node_defs_path.exists():
                with open(node_defs_path, 'r') as f:
                    node_definitions = load(f)
            else:
                node_definitions = {"categories": []}
            canvas = NodeCanvas(
                rel_pos=(0.251, 0.051),
                rel_size=(0.498, 0.648),
                reference_resolution=self.settings.saved_settings["resolution"],
                background_color=self.settings.saved_settings.get("backgroundcolor", [30, 30, 30]),
                node_definitions=node_definitions
            )
            canvas.update_layout(self.current_window_size)
            node_map = {}
            for node_data in pipeline_data.get("nodes", []):
                if node_data.get("node_type") == "input":
                    for node in canvas.nodes:
                        if node.node_type == "input":
                            node.rect.x = node_data["position"][0]
                            node.rect.y = node_data["position"][1]
                            node.update_connection_points()
                            node_map[node_data["id"]] = node
                            break
                elif node_data.get("node_type") == "output":
                    for node in canvas.nodes:
                        if node.node_type == "output":
                            node.rect.x = node_data["position"][0]
                            node.rect.y = node_data["position"][1]
                            node.update_connection_points()
                            node_map[node_data["id"]] = node
                            break
                else:
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
            for conn_data in pipeline_data.get("connections", []):
                from_node = node_map.get(conn_data["from_node"])
                to_node = node_map.get(conn_data["to_node"])
                to_param = conn_data.get("to_parameter")
                from_output = conn_data.get("from_output", "image")
                if from_node and to_node:
                    canvas.add_connection(from_node, to_node, to_param, from_output)
            self.viewport.set_pipeline_canvas(canvas)
            self.set_view_mode("pipeline")
            print(f"Loaded pipeline: {self.selected_pipeline.name}")
        except Exception as e:
            print(f"Error loading pipeline: {e}")
            import traceback
            traceback.print_exc()
        return
    
    def process_images(self):
        """Process selected images through the pipeline"""
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
        return
    
    def _process_images_thread(self, image_paths, pipeline_data):
        """Process images in a separate thread"""
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
                    "type": "progress",
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
            "type": "complete",
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
    
    def _save_documentation(self, save_path):
        """Save full documentation including inputs, outputs, code, and metadata"""
        try:
            doc_dir = save_path / f"processing_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            doc_dir.mkdir(exist_ok=True)
            input_dir = doc_dir / "inputs"
            input_dir.mkdir(exist_ok=True)
            for i, img_path in enumerate(self.selected_images):
                copy2(img_path, input_dir / img_path.name)
            output_dir = doc_dir / "outputs"
            output_dir.mkdir(exist_ok=True)
            for i, img in enumerate(self.output_images):
                image.save(img, str(output_dir / f"output_{i:04d}.png"))
            if self.selected_pipeline:
                copy2(self.selected_pipeline, doc_dir / "pipeline.json")
            metadata = {
                "processing_date": datetime.now().isoformat(),
                "num_inputs": len(self.selected_images),
                "num_outputs": len(self.output_images),
                "pipeline": str(self.selected_pipeline.name) if self.selected_pipeline else "None",
                "output_mode": self.settings.saved_settings.get("output_mode"),
                "camera": self.settings.saved_settings.get("camera"),
                "settings": self.settings.saved_settings
            }
            with open(doc_dir / "metadata.json", 'w') as f:
                dump(metadata, f, indent=2)
            readme = f"""# Processing Documentation
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Processing Details
- Input Images: {len(self.selected_images)}
- Output Images: {len(self.output_images)}
- Pipeline: {self.selected_pipeline.name if self.selected_pipeline else 'None'}
- Camera: {self.settings.saved_settings.get('camera', 'Unknown')}

## Directory Structure
- inputs/ : Original input images
- outputs/ : Processed output images
- pipeline.json : Processing pipeline used
- metadata.json : Complete processing metadata
"""
            with open(doc_dir / "README.md", 'w') as f:
                f.write(readme)
            print(f"Full documentation saved to: {doc_dir}")
        except Exception as e:
            print(f"Error saving documentation: {e}")
            print_exc()
        return
    
    def cleanup(self):
        """Cleanup scene resources"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        return