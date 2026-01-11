import os
from utils.logger import logger

class ProjectManager:
    def __init__(self):
        self.current_project_path = None

    def open_project(self, path):
        """Set the current project path"""
        if os.path.exists(path) and os.path.isdir(path):
            self.current_project_path = path
            logger.info(f"Opened project: {path}")
            return True
        else:
            logger.error(f"Invalid project path: {path}")
            return False

    def get_file_structure(self):
        """
        Get directory structure of the project
        Returns a nested dictionary representing the file tree
        """
        if not self.current_project_path:
            return {}

        file_tree = {"name": os.path.basename(self.current_project_path), "type": "dir", "path": self.current_project_path, "children": []}
        
        try:
            self._scan_dir(self.current_project_path, file_tree["children"])
        except Exception as e:
            logger.error(f"Error scanning project structure: {e}")
        
        return file_tree

    def _scan_dir(self, path, children_list):
        with os.scandir(path) as it:
            entries = sorted(list(it), key=lambda e: (not e.is_dir(), e.name))
            for entry in entries:
                # Skip hidden files and common ignore dirs
                if entry.name.startswith('.') or entry.name in ['__pycache__', 'node_modules', 'venv', 'env']:
                    continue
                
                node = {
                    "name": entry.name,
                    "path": entry.path,
                    "type": "dir" if entry.is_dir() else "file"
                }
                
                if entry.is_dir():
                    node["children"] = []
                    self._scan_dir(entry.path, node["children"])
                
                children_list.append(node)

project_manager = ProjectManager()
