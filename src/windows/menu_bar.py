from windows.base_window import BaseWindow
from UI.button import Button
'''
from tkinter import Tk,filedialog
from shutil import copy2
import json
from csv import DictWriter
from pathlib import Path
from pygame import image
from datetime import datetime
from traceback import print_exc
'''
from typing import Tuple

class MenuBar(BaseWindow):
    def __init__(
            self,
            scene_instance=None,
            scene="image_acquisition",
            rel_pos=(0.0, 0.0),
            rel_size=(1.0, 0.05),
            switch_scene_callback=None,
            call_methodes=[],
            s_font=None,
            fontsize=32,
            base_color=(70, 70, 200),
            hover_color=(100, 100, 240),
            text_color=(180, 180, 180),
            pressed_text_color=(255, 255, 255),
            disabled_color=(50, 50, 50),
            disabled_text_color=(100, 100, 100),
            border_radius=10,
            text_padding=10,
            reference_resolution=(1920, 1080)
            ):
        super().__init__(rel_pos, rel_size, reference_resolution)
        self.scene = scene
        self.switch_scene_callback = switch_scene_callback
        self.call_methodes = call_methodes
        self.s_font = s_font
        self.fontsize = fontsize
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.pressed_text_color = pressed_text_color
        self.disabled_color = disabled_color
        self.disabled_text_color = disabled_text_color
        self.border_radius = border_radius
        self.text_padding = text_padding
        self._setup_buttons()
        return

    def update_layout(self,window_size:Tuple[int,int])->None:
        super().update_layout(window_size)
        for button in self.menu_buttons:
            button.update_layout((self.window_width,self.window_height))
        return

    def handle_events(self,events:list)->None:
        self.handle_resize_events(events)
        for button in self.menu_buttons:
            button.handle_events(events)
        return

    def update(self)->None:
        pass

    def draw(self,screen)->None:
        for button in self.menu_buttons:
            button.draw(screen)
        return
    
    def _setup_buttons(self)->None:
        self.button_labels = ["Settings", "Image Acquisition", "Algorithms", "Processing"]
        self.callbacks = [
            lambda: self.switch_scene("settings"),
            lambda: self.switch_scene("image_acquisition"),
            lambda: self.switch_scene("algorithms"),
            lambda: self.switch_scene("processing")
        ]
        #When methodes are moved, change callbacks
        if self.scene == "settings":
            self.button_labels.append("Save Settings")
            self.button_labels.append("Close Application")
            self.callbacks.append(lambda: self.call_methodes[0]())
            self.callbacks.append(lambda: self.switch_scene("quit"))
        elif self.scene == "image_acquisition":
            self.button_labels.append("Load Images")
            self.button_labels.append("Save Images")
            self.callbacks.append(lambda: self.call_methodes[0]())
            self.callbacks.append(lambda: self.call_methodes[1]())
        elif self.scene == "algorithms":
            self.button_labels.append("Load Pipeline")
            self.button_labels.append("Save Pipeline")
            self.callbacks.append(lambda: self.call_methodes[0]())
            self.callbacks.append(lambda: self.call_methodes[1]())
        elif self.scene == "processing":
            self.button_labels.append("Load Images")
            self.button_labels.append("Save Output")
            self.callbacks.append(lambda: self.call_methodes[0]())
            self.callbacks.append(lambda: self.call_methodes[1]())
        self.menu_buttons = []
        layouts = self._positions(
            rows=1,
            cols=len(self.button_labels),
            rel_pos=self.rel_pos,
            rel_size=self.rel_size,
            gap=0.001
        )
        for i in range(len(self.button_labels)):
            button = Button(
                text=self.button_labels[i],
                rel_pos=layouts[i][0],
                rel_size=layouts[i][1],
                s_font=self.s_font,
                fontsize=self.fontsize,
                callback=self.callbacks[i],
                base_color=self.base_color,
                hover_color=self.hover_color,
                text_color=self.text_color,
                pressed_text_color=self.pressed_text_color,
                disabled_color=self.disabled_color,
                disabled_text_color=self.disabled_text_color,
                border_radius=self.border_radius,
                text_padding=self.text_padding,
                reference_resolution=self.reference_resolution
            )
            self.menu_buttons.append(button)
        #Deactivate the Button that the current Scene represents
        if self.scene == "settings":
            self.menu_buttons[0].set_enabled(False)
        elif self.scene == "image_acquisition":
            self.menu_buttons[1].set_enabled(False)
        elif self.scene == "algorithms":
            self.menu_buttons[2].set_enabled(False)
        elif self.scene == "processing":
            self.menu_buttons[3].set_enabled(False)
        return

    def switch_scene(self,call:str)->None:
        """Switch to a different scene"""
        self.switch_scene_callback(call)
        return

    def _positions(self,rows:int,cols:int,rel_pos:float,rel_size:float,gap:float)->list:
        """
        Calculate grid positions for buttons
        
        Args:
            rows: Number of rows
            cols: Number of columns
            rel_pos: Starting relative position
            rel_size: Total relative size
            gap: Gap between buttons
            
        Returns:
            List of (position, size) tuples
        """
        start_x, start_y = rel_pos
        total_w, total_h = rel_size
        total_gap_w = gap * (cols + 1)
        total_gap_h = gap * (rows + 1)
        btn_w = (total_w - total_gap_w) / cols
        btn_h = (total_h - total_gap_h) / rows
        layouts = []
        for r in range(rows):
            for c in range(cols):
                x = start_x + gap * (c + 1) + btn_w * c
                y = start_y + gap * (r + 1) + btn_h * r
                pos = (x, y)
                size = (btn_w, btn_h)
                layouts.append((pos, size))
        return layouts
    
    '''
    #Move to "processing" scene (maybe base class)
    def _load_images(self)->None:
        try:
            root = Tk()
            root.withdraw()
            working_dir = self.scene_instance.working_dir
            initial_dir = str(working_dir) if working_dir.exists() else None
            filepaths = filedialog.askopenfilenames(
                title="Select Images to Load",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                    ("All files", "*.*")
                ],
                initialdir=initial_dir
            )
            root.destroy()
            if not filepaths:
                return
            working_dir = self.scene_instance.working_dir
            if not working_dir.exists():
                working_dir.mkdir(parents=True)
            count = 0
            for filepath in filepaths:
                source_file = Path(filepath)
                copy2(source_file, working_dir / source_file.name)
                count += 1
            if count > 0:
                print(f"Loaded {count} images")
                self.scene_instance.file_viewer.load_directory(str(working_dir))
        except Exception as e:
            print(f"Error loading images: {e}")
        return
    
    #Move to "algorithm" scene
    def _load_pipeline(self):
        """Load a processing pipeline from a JSON file"""
        try:
            if not hasattr(self.scene_instance, 'working_dir'):
                print("Scene has no pipeline directory")
                return
            if not hasattr(self.scene_instance, '_deserialize_pipeline'):
                print("Scene cannot deserialize pipelines")
                return
            root = Tk()
            root.withdraw()
            initial_dir = str(self.scene_instance.working_dir) if self.scene_instance.working_dir.exists() else None
            filepath = filedialog.askopenfilename(
                title="Load Pipeline",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=initial_dir
            )
            root.destroy()
            if not filepath:
                return
            with open(filepath, 'r') as f:
                pipeline_data = json.load(f)
            self.scene_instance._deserialize_pipeline(pipeline_data)
            print(f"Pipeline loaded from: {filepath}")
        except Exception as e:
            print(f"Error loading pipeline: {e}")
            print_exc()
        return

    #Move to "algorithm" scene
    def _save_pipeline(self):
        """Save the current processing pipeline to a JSON file"""
        try:
            if not hasattr(self.scene_instance, 'working_dir'):
                print("Scene has no pipeline directory")
                return
            if not hasattr(self.scene_instance, '_serialize_pipeline'):
                print("Scene cannot serialize pipelines")
                return
            root = Tk()
            root.withdraw()
            initial_dir = str(self.scene_instance.working_dir) if self.scene_instance.working_dir.exists() else None
            filepath = filedialog.asksaveasfilename(
                title="Save Pipeline",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir=initial_dir
            )
            root.destroy()
            if not filepath:
                return
            pipeline_data = self.scene_instance._serialize_pipeline()
            with open(filepath, 'w') as f:
                json.dump(pipeline_data, f, indent=2)
            print(f"Pipeline saved to: {filepath}")
            if hasattr(self.scene_instance, 'file_viewer'):
                self.scene_instance.file_viewer.load_directory(str(self.scene_instance.working_dir))
        except Exception as e:
            print(f"Error saving pipeline: {e}")
        return
    
    #Move to "processing" scene
    def _save_output(self):
        try:
            output_images = self.scene_instance.output_images
            if not output_images:
                print("No outputs to save")
                return
            output_mode = self.scene_instance.settings.saved_settings.get("output_mode", "Images Only")
            root = Tk()
            root.withdraw()
            output_dir = self.scene_instance.output_dir if hasattr(self.scene_instance, 'output_dir') else Path.cwd() / "processed_outputs"
            initial_dir = str(output_dir) if output_dir.exists() else None
            if output_mode == "Images Only":
                filepath = filedialog.asksaveasfilename(
                    title="Save Output Images As (will add numbers)",
                    defaultextension=".png",
                    filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                    initialdir=initial_dir,
                    initialfile="processed_001.png"
                )
                root.destroy()
                if filepath:
                    save_path = Path(filepath).parent
                    self._save_images_only(output_images, save_path)
            elif output_mode == "Full Documentation":
                save_dir = filedialog.askdirectory(
                    title="Select Directory for Full Documentation",
                    initialdir=initial_dir
                )
                root.destroy()
                if save_dir:
                    self._save_full_documentation(output_images, Path(save_dir))
            elif output_mode == "Data Only":
                filepath = filedialog.asksaveasfilename(
                    title="Save Data As",
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    initialdir=initial_dir,
                    initialfile="data.json"
                )
                root.destroy()
                if filepath:
                    save_path = Path(filepath).parent
                    self._save_data_only(output_images, save_path)
            else:
                root.destroy()
                print(f"Unknown output mode: {output_mode}")
        except Exception as e:
            print(f"Error saving output: {e}")
            print_exc()
        return
    
    #Move to "processing" scene
    def _save_images_only(self, output_images, save_path):
        """Save only the processed images"""
        for i, img in enumerate(output_images):
            filename = f"processed_{i:04d}.png"
            image.save(img, str(save_path / filename))
        print(f"Saved {len(output_images)} images to {save_path}")
        return
    
    #Move to "processing" scene
    def _save_full_documentation(self, output_images, save_path):
        """Save images with full documentation"""
        doc_dir = save_path / f"processing_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        doc_dir.mkdir(exist_ok=True)
        input_dir = doc_dir / "inputs"
        output_dir = doc_dir / "outputs"
        input_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)
        for i, img in enumerate(output_images):
            filename = f"output_{i:04d}.png"
            image.save(img, str(output_dir / filename))
        if hasattr(self.scene_instance, 'selected_images'):
            for img_path in self.scene_instance.selected_images:
                if Path(img_path).exists():
                    copy2(img_path, input_dir / Path(img_path).name)
        if hasattr(self.scene_instance, 'selected_pipeline') and self.scene_instance.selected_pipeline:
            copy2(self.scene_instance.selected_pipeline, doc_dir / "pipeline.json")
            if hasattr(self.scene_instance, 'output_data') and self.scene_instance.output_data:
                data_dir = doc_dir / "data"
                data_dir.mkdir(exist_ok=True)
                all_data = []
                for item in self.scene_instance.output_data:
                    if item.get("data") is not None:
                        all_data.append(item)
                if all_data:
                    with open(data_dir / "object_data.json", 'w') as f:
                        json.dump(all_data, f, indent=2)
                    for item in all_data:
                        if item.get("data") and isinstance(item["data"], list) and len(item["data"]) > 0:
                            csv_filename = data_dir / f"{Path(item['image_name']).stem}_data.csv"
                            with open(csv_filename, 'w', newline='') as csvfile:
                                fieldnames = list(item["data"][0].keys())
                                writer = DictWriter(csvfile, fieldnames=fieldnames)
                                writer.writeheader()
                                for obj in item["data"]:
                                    writer.writerow(obj)
            metadata = {
                "processing_date": datetime.now().isoformat(),
                "num_outputs": len(output_images),
                "output_mode": "Full Documentation",
                "has_data": hasattr(self.scene_instance, 'output_data') and len(self.scene_instance.output_data) > 0
            }
            if hasattr(self.scene_instance, 'settings'):
                metadata["settings"] = self.scene_instance.settings.saved_settings
            with open(doc_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
        has_data = hasattr(self.scene_instance, 'output_data') and len(self.scene_instance.output_data) > 0
        readme = f"""# Processing Documentation
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Contents
- inputs/ : Original input images
- outputs/ : Processed output images
- pipeline.json : Processing pipeline configuration
- metadata.json : Processing metadata and settings
{"- data/ : Object characteristics and analysis data (JSON and CSV formats)" if has_data else ""}

## Summary
- Output Images: {len(output_images)}
{"- Data files: Available in data/ directory" if has_data else ""}

{"## Data Format" if has_data else ""}
{"The data directory contains:" if has_data else ""}
{"- object_data.json : All object data in JSON format" if has_data else ""}
{"- *_data.csv : Individual CSV files for each processed image" if has_data else ""}
"""
        with open(doc_dir / "README.md", 'w') as f:
            f.write(readme)
        print(f"Saved full documentation to: {doc_dir}")
        return
    
    #Move to "processing" scene
    def _save_data_only(self, output_images, save_path):
        """Save only data without images"""
        data_dir = save_path / f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        data_dir.mkdir(exist_ok=True)
        
        if not hasattr(self.scene_instance, 'output_data'):
            print("No data available to save")
            return
        
        all_data = []
        for item in self.scene_instance.output_data:
            data = item.get("data")
            if data is not None and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                all_data.append(item)
        
        if not all_data:
            print("No valid object characteristics data found to export")
            print("Make sure your pipeline includes 'Object Characteristics' node connected to the Output node's 'data' input")
            return
        
        # Save CSV files only
        csv_count = 0
        for item in all_data:
            data = item.get("data")
            csv_filename = data_dir / f"{Path(item['image_name']).stem}_data.csv"
            
            try:
                with open(csv_filename, 'w', newline='') as csvfile:
                    fieldnames = list(data[0].keys())
                    writer = DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for obj in data:
                        row = {}
                        for key, value in obj.items():
                            if isinstance(value, tuple):
                                row[key] = str(value)
                            elif hasattr(value, 'tolist'):
                                row[key] = str(value.tolist())
                            else:
                                row[key] = value
                        writer.writerow(row)
                
                csv_count += 1
                print(f"Created CSV: {csv_filename}")
            except Exception as e:
                print(f"Error writing CSV for {item['image_name']}: {e}")
                print_exc()
        
        if csv_count > 0:
            print(f"Saved {csv_count} CSV files to: {data_dir}")
        else:
            print("No valid data found to export")
        return
    
    def _save_settings(self):
        """Save settings from the settings scene"""
        self.save_settings_callback()
        return
    '''