from PyQt6.QtWidgets import (QTreeWidget, QTreeWidgetItem, QWidget, QVBoxLayout, QLabel,
                             QAbstractItemView)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDrag, QIcon
from engine.nodes.opencv_nodes import NodeRegistry

class NodeToolbox(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel("Node Library")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-weight: bold; padding: 5px;")
        self.layout.addWidget(self.label)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setDragEnabled(True)
        self.tree_widget.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.layout.addWidget(self.tree_widget)
        
        self.populate()

    def populate(self):
        types = NodeRegistry.get_all_types()
        
        # Categories mapping (Simple heuristic for now)
        categories = {
            "Input": ["Read"],
            "Process": ["Convert", "Blur", "Canny", "GenericFunction"],
            "Output": ["Show"],
            "Other": []
        }
        
        category_items = {}
        for cat in categories:
            item = QTreeWidgetItem(self.tree_widget)
            item.setText(0, cat)
            item.setExpanded(True)
            category_items[cat] = item
            
        for t in types:
            # Determine category
            found = False
            for cat, keywords in categories.items():
                if any(k in t for k in keywords):
                    parent = category_items[cat]
                    item = QTreeWidgetItem(parent)
                    item.setText(0, t)
                    # Add icon based on category (placeholders)
                    # item.setIcon(0, QIcon("path/to/icon.png"))
                    found = True
                    break
            
            if not found:
                parent = category_items["Other"]
                item = QTreeWidgetItem(parent)
                item.setText(0, t)
