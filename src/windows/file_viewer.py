from pygame import (Rect, draw, mouse, MOUSEBUTTONDOWN, MOUSEWHEEL, K_DELETE, KEYDOWN, key,
                    K_F2, K_c, K_x, K_v, KMOD_CTRL)
from pathlib import Path
from datetime import datetime
from shutil import copy2, move, rmtree
from windows.base_window import BaseWindow
from tkinter import Tk, simpledialog
from typing import Tuple, List, Optional

class FileItem:
    """Represents a file or folder in the file viewer"""
    def __init__(self, path: Path, is_folder: bool = False, depth: int = 0):
        self.path = path
        self.is_folder = is_folder
        self.depth = depth
        self.expanded = False
        self.selected = False
        self.rect = Rect(0, 0, 0, 0)
        self.name = self.path.name if self.path.name else str(self.path)
        return
    
    def toggle_expanded(self) -> bool:
        """Toggle folder expanded state"""
        if self.is_folder:
            self.expanded = not self.expanded
        return self.expanded

class FileViewer(BaseWindow):
    # Image file extensions that can be displayed
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}
    
    def __init__(self, 
                 rel_pos: Tuple[float, float] = (0.661, 0.051),
                 rel_size: Tuple[float, float] = (0.338, 0.948),
                 reference_resolution: Tuple[int, int] = (1920, 1080),
                 background_color: Tuple[int, int, int] = (40, 40, 40),
                 folder_color: Tuple[int, int, int] = (100, 150, 200),
                 file_color: Tuple[int, int, int] = (200, 200, 200),
                 selected_color: Tuple[int, int, int] = (80, 120, 160),
                 hover_color: Tuple[int, int, int] = (60, 60, 80),
                 text_color: Tuple[int, int, int] = (255, 255, 255),
                 line_height: int = 30):
        """
        Initialize the FileViewer window
        
        Args:
            rel_pos: Relative position (x, y) as fraction of window size
            rel_size: Relative size (width, height) as fraction of window size
            reference_resolution: Reference resolution for scaling
            background_color: RGB color for background
            folder_color: RGB color for folder icons
            file_color: RGB color for file icons
            selected_color: RGB color for selected items
            hover_color: RGB color for hovered items
            text_color: RGB color for text
            line_height: Base height of each line in pixels
        """
        super().__init__(rel_pos, rel_size, reference_resolution, background_color)
        self.folder_color = folder_color
        self.file_color = file_color
        self.selected_color = selected_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.line_height = line_height
        self.indent_width = 20
        self.root_path = None
        self.items: List[FileItem] = []
        self.visible_items: List[FileItem] = []
        self.selected_item: Optional[FileItem] = None
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 30
        self.hovered_item: Optional[FileItem] = None
        self.clipboard: List[Path] = []
        self.clipboard_mode: Optional[str] = None
        return

    def update_layout(self, window_size: Tuple[int, int]) -> None:
        """
        Update file viewer size and position based on window size
        
        Args:
            window_size: Tuple of (width, height) representing window dimensions
        """
        super().update_layout(window_size)
        scale_factor = self.get_scale_factor()
        self.line_height = max(20, int(30 * scale_factor))
        self.indent_width = max(15, int(20 * scale_factor))
        total_height = len(self.visible_items) * self.line_height
        self.max_scroll = max(0, total_height - self.rect.height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)
        return
    
    def update(self) -> None:
        """Update the file viewer state (called every frame)"""
        mouse_pos = mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            relative_y = mouse_pos[1] - self.rect.y + self.scroll_offset
            item_index = int(relative_y // self.line_height)
            if 0 <= item_index < len(self.visible_items):
                self.hovered_item = self.visible_items[item_index]
            else:
                self.hovered_item = None
        else:
            self.hovered_item = None
        return
    
    def handle_events(self, events: list) -> None:
        """
        Handle pygame events
        
        Args:
            events: List of pygame events
        """
        self.handle_resize_events(events)
        for event in events:
            if event.type == MOUSEWHEEL:
                self._handle_scroll(event)
            elif event.type == MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)
            elif event.type == KEYDOWN:
                self._handle_keyboard(event)
        return
    
    def draw(self, surface) -> None:
        """
        Draw the file viewer to the screen
        
        Args:
            surface: Pygame surface to draw on
        """
        draw.rect(surface, self.background_color, self.rect)
        draw.rect(surface, (100, 100, 100), self.rect, 2)
        clip_rect = surface.get_clip()
        surface.set_clip(self.rect)
        y_offset = self.rect.y - self.scroll_offset
        for item in self.visible_items:
            item_rect = Rect(
                self.rect.x,
                y_offset,
                self.rect.width,
                self.line_height
            )
            if item_rect.bottom < self.rect.y or item_rect.top > self.rect.bottom:
                y_offset += self.line_height
                continue
            if item == self.selected_item:
                draw.rect(surface, self.selected_color, item_rect)
            elif item == self.hovered_item:
                draw.rect(surface, self.hover_color, item_rect)
            self._draw_item_icon(surface, item, y_offset)
            self._draw_item_text(surface, item, y_offset)
            y_offset += self.line_height
        surface.set_clip(clip_rect)
        if self.max_scroll > 0:
            self._draw_scrollbar(surface)
        return
    
    def _handle_scroll(self, event) -> None:
        """Handle mouse wheel scrolling"""
        if self.rect.collidepoint(event.pos) if hasattr(event, 'pos') else True:
            self.scroll_offset -= event.y * self.scroll_speed
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        return
    
    def _handle_mouse_click(self, event) -> None:
        """Handle mouse button clicks"""
        if not self.rect.collidepoint(event.pos):
            return
        relative_y = event.pos[1] - self.rect.y + self.scroll_offset
        item_index = int(relative_y // self.line_height)
        if 0 <= item_index < len(self.visible_items):
            clicked_item = self.visible_items[item_index]
            relative_x = event.pos[0] - self.rect.x
            icon_x = clicked_item.depth * self.indent_width
            if clicked_item.is_folder and icon_x <= relative_x <= icon_x + self.indent_width:
                if clicked_item.expanded:
                    self.collapse_folder(clicked_item)
                else:
                    self.expand_folder(clicked_item)
            else:
                if event.button == 1:
                    if self.selected_item == clicked_item:
                        self.selected_item = None
                    else:
                        self.selected_item = clicked_item
        return
    
    def _handle_keyboard(self, event) -> None:
        """Handle keyboard shortcuts"""
        if event.key == K_DELETE and self.selected_item:
            self.delete_selected()
        elif event.key == K_F2 and self.selected_item:
            self.rename_selected()
        elif event.key == K_c and key.get_mods() & KMOD_CTRL:
            self.copy_selected()
        elif event.key == K_x and key.get_mods() & KMOD_CTRL:
            self.cut_selected()
        elif event.key == K_v and key.get_mods() & KMOD_CTRL:
            self.paste_clipboard()
        return
        
    def load_directory(self, path):
        self.root_path = Path(path)
        self.items = []
        self.selected_items = []
        self.scroll_offset = 0
        if self.root_path.exists():
            self._scan_directory(self.root_path, depth=0)
            self._update_visible_items()
        return
        
    def _scan_directory(self, directory, depth=0):
        if not directory.exists() or not directory.is_dir():
            return
        try:
            entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            for entry in entries:
                if entry.is_dir():
                    item = FileItem(entry, is_folder=True, depth=depth)
                    self.items.append(item)
                elif entry.suffix.lower() in self.image_extensions:
                    item = FileItem(entry, is_folder=False, depth=depth)
                    self.items.append(item)
        except PermissionError:
            pass
        return
    
    def _update_visible_items(self):
        self.visible_items = []
        expanded_paths = set()
        for item in self.items:
            if item.depth == 0:
                self.visible_items.append(item)
                if item.is_folder and item.expanded:
                    expanded_paths.add(item.path)
            else:
                is_visible = True
                for ancestor_item in self.items:
                    if ancestor_item.is_folder and ancestor_item.path in item.path.parents:
                        if not ancestor_item.expanded:
                            is_visible = False
                            break
                if is_visible:
                    self.visible_items.append(item)
                    if item.is_folder and item.expanded:
                        expanded_paths.add(item.path)
        total_height = len(self.visible_items) * self.line_height
        self.max_scroll = max(0, total_height - self.rect.height)
        return
    
    def _draw_item_icon(self, surface, item: FileItem, y_offset: int) -> None:
        """Draw icon for file or folder"""
        indent = item.depth * self.indent_width
        icon_rect = Rect(
            self.rect.x + indent + 5,
            y_offset + self.line_height // 4,
            self.line_height // 2,
            self.line_height // 2
        )
        if item.is_folder:
            if item.expanded:
                points = [
                    (icon_rect.centerx, icon_rect.bottom - 2),
                    (icon_rect.left + 2, icon_rect.top + 2),
                    (icon_rect.right - 2, icon_rect.top + 2)
                ]
            else:
                points = [
                    (icon_rect.right - 2, icon_rect.centery),
                    (icon_rect.left + 2, icon_rect.top + 2),
                    (icon_rect.left + 2, icon_rect.bottom - 2)
                ]
            draw.polygon(surface, self.folder_color, points)
        else:
            draw.rect(surface, self.file_color, icon_rect, 2)
        return
    
    def _draw_item_text(self, surface, item: FileItem, y_offset: int) -> None:
        """Draw text label for item"""
        indent = item.depth * self.indent_width
        text_x = self.rect.x + indent + self.indent_width + 5
        text = self.font.render(item.name, True, self.text_color)
        max_width = self.rect.width - (text_x - self.rect.x) - 10
        if text.get_width() > max_width:
            truncated_name = item.name
            while len(truncated_name) > 0:
                text = self.font.render(truncated_name + "...", True, self.text_color)
                if text.get_width() <= max_width:
                    break
                truncated_name = truncated_name[:-1]
        text_y = y_offset + (self.line_height - text.get_height()) // 2
        surface.blit(text, (text_x, text_y))
        return
    
    def _draw_scrollbar(self, surface) -> None:
        """Draw scrollbar on the right side"""
        scrollbar_height = max(20, int(self.rect.height * (self.rect.height / (len(self.visible_items) * self.line_height))))
        scrollbar_y = self.rect.y + int((self.scroll_offset / self.max_scroll) * (self.rect.height - scrollbar_height))
        scrollbar_rect = Rect(
            self.rect.right - 10,
            scrollbar_y,
            8,
            scrollbar_height
        )
        draw.rect(surface, (150, 150, 150), scrollbar_rect, border_radius=4)
        return
    
    def load_directory(self, path: str) -> None:
        """
        Load a directory and display its contents
        
        Args:
            path: Path to directory to load
        """
        self.root_path = Path(path)
        self.items = []
        self.selected_item = None
        self.scroll_offset = 0
        if self.root_path.exists():
            self._scan_directory(self.root_path, depth=0)
            self._update_visible_items()
        return
    
    def _scan_directory(self, directory: Path, depth: int = 0) -> None:
        """
        Recursively scan directory and create FileItem objects
        
        Args:
            directory: Directory path to scan
            depth: Current nesting depth
        """
        if not directory.exists() or not directory.is_dir():
            return
        try:
            entries = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
            
            for entry in entries:
                if entry.is_dir():
                    item = FileItem(entry, is_folder=True, depth=depth)
                    self.items.append(item)
                elif entry.suffix.lower() in self.IMAGE_EXTENSIONS:
                    item = FileItem(entry, is_folder=False, depth=depth)
                    self.items.append(item)
        except PermissionError as e:
            print(f"Permission denied accessing {directory}: {e}")
        return
    
    def _update_visible_items(self) -> None:
        """Update the list of visible items based on folder expansion state"""
        self.visible_items = []
        for item in self.items:
            if item.depth == 0:
                self.visible_items.append(item)
            else:
                is_visible = True
                for ancestor_item in self.items:
                    if ancestor_item.is_folder and ancestor_item.path in item.path.parents:
                        if not ancestor_item.expanded:
                            is_visible = False
                            break
                if is_visible:
                    self.visible_items.append(item)
        total_height = len(self.visible_items) * self.line_height
        self.max_scroll = max(0, total_height - self.rect.height)
        return
    
    def expand_folder(self, folder_item: FileItem) -> None:
        """
        Expand a folder to show its contents
        
        Args:
            folder_item: Folder to expand
        """
        if not folder_item.is_folder or folder_item.expanded:
            return
        folder_item.expanded = True
        insert_index = self.items.index(folder_item) + 1
        try:
            entries = sorted(folder_item.path.iterdir(), 
                           key=lambda x: (not x.is_dir(), x.name.lower()))
            new_items = []
            for entry in entries:
                if entry.is_dir():
                    new_items.append(FileItem(entry, is_folder=True, depth=folder_item.depth + 1))
                elif entry.suffix.lower() in self.IMAGE_EXTENSIONS:
                    new_items.append(FileItem(entry, is_folder=False, depth=folder_item.depth + 1))
            for i, item in enumerate(new_items):
                self.items.insert(insert_index + i, item)
        except PermissionError as e:
            print(f"Permission denied expanding {folder_item.path}: {e}")
        self._update_visible_items()
        return
    
    def collapse_folder(self, folder_item: FileItem) -> None:
        """
        Collapse a folder to hide its contents
        
        Args:
            folder_item: Folder to collapse
        """
        if not folder_item.is_folder or not folder_item.expanded:
            return
        folder_item.expanded = False
        children_to_remove = []
        for item in self.items:
            if folder_item.path in item.path.parents:
                children_to_remove.append(item)
        for child in children_to_remove:
            self.items.remove(child)
            if child == self.selected_item:
                self.selected_item = None
        self._update_visible_items()
        return
    
    def delete_selected(self) -> None:
        """Delete the currently selected file or folder"""
        if not self.selected_item:
            return
        try:
            if self.selected_item.path.exists():
                if self.selected_item.is_folder:
                    rmtree(self.selected_item.path)
                else:
                    self.selected_item.path.unlink()
                self.items.remove(self.selected_item)
                self.selected_item = None
                self._update_visible_items()
                print(f"Deleted: {self.selected_item.path.name}")
        except Exception as e:
            print(f"Error deleting {self.selected_item.path}: {e}")
        return
    
    def rename_selected(self) -> None:
        """Rename the selected file/folder"""
        if not self.selected_item:
            print("No item selected to rename")
            return
        new_name = self._get_user_input_for_rename(self.selected_item.name)
        if new_name and new_name != self.selected_item.name:
            try:
                new_path = self.selected_item.path.parent / new_name
                self.selected_item.path.rename(new_path)
                self.selected_item.path = new_path
                self.selected_item.name = new_name
                self._update_visible_items()
                print(f"Renamed to: {new_name}")
            except Exception as e:
                print(f"Error renaming: {e}")
        return

    def copy_selected(self) -> None:
        """Copy selected file to clipboard"""
        if not self.selected_item or self.selected_item.is_folder:
            return
        self.clipboard = [self.selected_item.path]
        self.clipboard_mode = "copy"
        print(f"Copied: {self.selected_item.path.name}")
        return

    def cut_selected(self) -> None:
        """Cut selected file to clipboard"""
        if not self.selected_item or self.selected_item.is_folder:
            return
        self.clipboard = [self.selected_item.path]
        self.clipboard_mode = "cut"
        print(f"Cut: {self.selected_item.path.name}")
        return

    def paste_clipboard(self) -> None:
        """Paste files from clipboard to current directory"""
        if not self.clipboard or not self.root_path:
            return
        for path in self.clipboard:
            try:
                destination = self.root_path / path.name
                if self.clipboard_mode == "copy":
                    copy2(path, destination)
                    print(f"Copied {path.name} to {self.root_path}")
                elif self.clipboard_mode == "cut":
                    move(str(path), str(destination))
                    print(f"Moved {path.name} to {self.root_path}")
            except Exception as e:
                print(f"Error pasting {path.name}: {e}")
        if self.clipboard_mode == "cut":
            self.clipboard = []
            self.clipboard_mode = None
        self.load_directory(str(self.root_path))
        return

    def create_new_folder(self) -> None:
        """Create a new folder in current directory"""
        if not self.root_path:
            return
        folder_name = self._get_user_input_for_new_folder()
        if folder_name:
            try:
                new_folder = self.root_path / folder_name
                new_folder.mkdir(exist_ok=False)
                self.load_directory(str(self.root_path))
                print(f"Created folder: {folder_name}")
            except FileExistsError:
                print(f"Folder '{folder_name}' already exists")
            except Exception as e:
                print(f"Error creating folder: {e}")
        return
    
    def get_selected_files(self) -> List[Path]:
        """
        Get list of selected files (not folders)
        
        Returns:
            List of Path objects for selected files
        """
        if self.selected_item and not self.selected_item.is_folder:
            return [self.selected_item.path]
        return []
    
    def get_item_info(self) -> Optional[dict]:
        """
        Get info about selected item
        
        Returns:
            Dictionary with item information or None
        """
        if not self.selected_item:
            return None
        try:
            stat = self.selected_item.path.stat()
            info = {
                'name': self.selected_item.name,
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'is_folder': self.selected_item.is_folder
            }
            return info
        except Exception as e:
            print(f"Error getting item info: {e}")
            return None
    
    def _get_user_input_for_rename(self, current_name: str) -> Optional[str]:
        """
        Show dialog to get new name for file/folder
        
        Args:
            current_name: Current name of the item
            
        Returns:
            New name or None if cancelled
        """
        root = Tk()
        root.withdraw()
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=current_name)
        root.destroy()
        return new_name
    
    def _get_user_input_for_new_folder(self) -> Optional[str]:
        """
        Show dialog to get name for new folder
        
        Returns:
            Folder name or None if cancelled
        """
        root = Tk()
        root.withdraw()
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        root.destroy()
        return folder_name