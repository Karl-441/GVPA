import os
import shutil
from typing import List, Optional

def ensure_dir(path: str):
    """Ensure directory exists"""
    if not os.path.exists(path):
        os.makedirs(path)

def list_files(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
    """List files in directory with optional extension filter"""
    if not os.path.exists(directory):
        return []
    
    files = []
    for f in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, f)):
            if extensions:
                if any(f.lower().endswith(ext.lower()) for ext in extensions):
                    files.append(os.path.join(directory, f))
            else:
                files.append(os.path.join(directory, f))
    return files

def save_text(content: str, path: str):
    """Save text content to file"""
    ensure_dir(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def load_text(path: str) -> str:
    """Load text content from file"""
    if not os.path.exists(path):
        return ""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
