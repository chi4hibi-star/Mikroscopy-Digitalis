from pygame import (Rect,draw,mouse,MOUSEBUTTONDOWN,MOUSEWHEEL,K_DELETE,KEYDOWN,key,
                    K_F2,K_a,K_c,K_x,K_v,KMOD_CTRL)
from pathlib import Path
from platform import system
from datetime import datetime
from os import startfile
from shutil import copy2, move, rmtree
from windows.base_window import BaseWindow
from tkinter import Tk, simpledialog

class FileItem:
    def __init__(self, path, is_folder=False, depth=0):
        self.path = Path(path)
        self.is_folder = is_folder
        self.depth = depth
        self.expanded = False
        self.selected = False
        self.rect = Rect(0, 0, 0, 0)
        self.name = self.path.name if self.path.name else str(self.path)
        return
    
    def toggle_expanded(self):
        if self.is_folder:
            self.expanded = not self.expanded
        return self.expanded

class FileViewer(BaseWindow):
    def __init__(self, 
                 rel_pos=(0.661, 0.051),
                 rel_size=(0.338, 0.948),
                 reference_resolution=(1920, 1080),
                 background_color=(40, 40, 40),
                 folder_color=(100, 150, 200),
                 file_color=(200, 200, 200),
                 selected_color=(80, 120, 160),
                 hover_color=(60, 60, 80),
                 text_color=(255, 255, 255),
                 line_height=30):
        super().__init__(rel_pos, rel_size, reference_resolution, background_color)
        self.folder_color = folder_color
        self.file_color = file_color
        self.selected_color = selected_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.line_height = line_height
        self.indent_width = 20
        self.root_path = None
        self.items = []
        self.visible_items = []
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 30
        self.hovered_item = None
        self.selected_items = []
        self.image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.webp'}
        return

    def update_layout(self, window_size):
        super().update_layout(window_size)
        scale_factor = self.get_scale_factor()
        self.line_height = max(20, int(30 * scale_factor))
        self.indent_width = max(15, int(20 * scale_factor))
        total_height = len(self.visible_items) * self.line_height
        self.max_scroll = max(0, total_height - self.rect.height)
        self.scroll_offset = min(self.scroll_offset, self.max_scroll)
        return
    
    def update(self):
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
    
    def handle_events(self, events):
        self.handle_resize_events(events)
        for event in events:
            if event.type == MOUSEWHEEL:
                if self.rect.collidepoint(event.pos) if hasattr(event, 'pos') else True:
                    self.scroll_offset -= event.y * self.scroll_speed
                    self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
            elif event.type == MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
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
                                if clicked_item in self.selected_items:
                                    self.selected_items.remove(clicked_item)
                                else:
                                    self.selected_items.append(clicked_item)
            elif event.type == KEYDOWN:
                if event.key == K_DELETE and self.selected_items:
                    self.delete_selected()
                elif event.key == K_F2 and self.selected_items:
                    self.rename_selected()
                elif event.key == K_a and key.get_mods() & KMOD_CTRL:
                    self.select_all()
                elif event.key == K_c and key.get_mods() & KMOD_CTRL:
                    self.copy_selected()
                elif event.key == K_x and key.get_mods() & KMOD_CTRL:
                    self.cut_selected()
                elif event.key == K_v and key.get_mods() & KMOD_CTRL:
                    self.paste_clipboard()
        return
    
    def draw(self, surface):
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
            if item in self.selected_items:
                draw.rect(surface, self.selected_color, item_rect)
            elif item == self.hovered_item:
                draw.rect(surface, self.hover_color, item_rect)
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
            y_offset += self.line_height
        surface.set_clip(clip_rect)
        if self.max_scroll > 0:
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
    
    def expand_folder(self, folder_item):
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
                elif entry.suffix.lower() in self.image_extensions:
                    new_items.append(FileItem(entry, is_folder=False, depth=folder_item.depth + 1))
            for i, item in enumerate(new_items):
                self.items.insert(insert_index + i, item)
        except PermissionError:
            pass
        self._update_visible_items()
        return
    
    def collapse_folder(self, folder_item):
        if not folder_item.is_folder or not folder_item.expanded:
            return
        folder_item.expanded = False
        children_to_remove = []
        for item in self.items:
            if folder_item.path in item.path.parents:
                children_to_remove.append(item)
        for child in children_to_remove:
            self.items.remove(child)
            if child in self.selected_items:
                self.selected_items.remove(child)
        self._update_visible_items()
        return
    
    def delete_selected(self):
        for item in self.selected_items[:]:
            try:
                if item.path.exists():
                    if item.is_folder:
                        rmtree(item.path)
                    else:
                        item.path.unlink()
                    self.items.remove(item)
                    self.selected_items.remove(item)
            except Exception as e:
                print(f"Error deleting {item.path}: {e}")
        self._update_visible_items()
        return
    
    def get_selected_files(self):
        return [item.path for item in self.selected_items if not item.is_folder]
    
    def rename_selected(self):
        """Rename the selected file/folder - opens dialog for new name"""
        if len(self.selected_items) != 1:
            print("Select exactly one item to rename")
            return
        item = self.selected_items[0]
        new_name = self._get_user_input_for_rename(item.name)
        if new_name and new_name != item.name:
            try:
                new_path = item.path.parent / new_name
                item.path.rename(new_path)
                item.path = new_path
                item.name = new_name
                self._update_visible_items()
                print(f"Renamed to: {new_name}")
            except Exception as e:
                print(f"Error renaming: {e}")
        return

    def copy_selected(self):
        """Copy selected files to clipboard (internal)"""
        self.clipboard = [item.path for item in self.selected_items if not item.is_folder]
        self.clipboard_mode = "copy"
        print(f"Copied {len(self.clipboard)} items")
        return

    def cut_selected(self):
        """Cut selected files to clipboard (internal)"""
        self.clipboard = [item.path for item in self.selected_items if not item.is_folder]
        self.clipboard_mode = "cut"
        print(f"Cut {len(self.clipboard)} items")
        return

    def paste_clipboard(self):
        """Paste files from clipboard to current directory"""
        if not hasattr(self, 'clipboard') or not self.clipboard:
            return
        for path in self.clipboard:
            try:
                if self.clipboard_mode == "copy":
                    copy2(path, self.root_path / path.name)
                else:
                    move(str(path), str(self.root_path / path.name))
            except Exception as e:
                print(f"Error pasting {path.name}: {e}")
        if self.clipboard_mode == "cut":
            self.clipboard = []
        self.load_directory(str(self.root_path))
        return

    def create_new_folder(self):
        """Create a new folder in current directory"""
        folder_name = self._get_user_input_for_new_folder()
        if folder_name:
            try:
                new_folder = self.root_path / folder_name
                new_folder.mkdir(exist_ok=False)
                self.load_directory(str(self.root_path))
                print(f"Created folder: {folder_name}")
            except Exception as e:
                print(f"Error creating folder: {e}")
        return

    def open_in_explorer(self):
        """Open selected item in system file explorer"""
        if len(self.selected_items) != 1:
            return
        path = str(self.selected_items[0].path)
        
        if system() == "Windows":
            startfile(path)
        elif system() == "Darwin":
            system(f'open "{path}"')
        else:
            system(f'xdg-open "{path}"')
        return

    def select_all(self):
        """Select all visible items"""
        self.selected_items = self.visible_items.copy()
        return

    def deselect_all(self):
        """Clear selection"""
        self.selected_items = []
        return

    def get_item_info(self):
        """Get info about selected item (size, modified date, etc)"""
        if len(self.selected_items) != 1:
            return None
        item = self.selected_items[0]
        stat = item.path.stat()
        info = {
            'name': item.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'is_folder': item.is_folder
        }
        return info
    
    def _get_user_input_for_rename(self, current_name):
        root = Tk()
        root.withdraw()
        new_name = simpledialog.askstring("Rename", "Enter new name:", initialvalue=current_name)
        root.destroy()
        return new_name