from PyQt6.QtWidgets import (QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem, 
                             QGraphicsProxyWidget, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QMenu)
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPainterPath, QFont, QRadialGradient, QFontMetrics, QLinearGradient
import math
import os
from utils.logger import logger
from core.options_manager import options_manager

# Nord Color Palette
COLORS = {
    "background": "#2E3440", 
    "body": "#3B4252",
    "border": "#4C566A",
    "text": "#ECEFF4",
    "text_dim": "#D8DEE9",
    "header_default": "#5E81AC",
    "header_api": "#B48EAD",
    "header_event": "#EBCB8B",
    "header_module": "#8FBCBB",
    "socket_in": "#A3BE8C",
    "socket_out": "#88C0D0",
    "edge_default": "#D8DEE9",
    "edge_api": "#B48EAD",
    "edge_event": "#EBCB8B",
    "edge_flow": "#A3BE8C",
    "edge_module": "#8FBCBB",
    "edge_io": "#5E81AC",
    "shadow": "#1A1E24"
}

# Minimal Color Palette (6 colors)
MINIMAL_COLORS = {
    "FRONTEND": "#E3F2FD",      # Light Blue
    "LOCAL_SERVICE": "#E8F5E9", # Light Green
    "LOCAL_INFRA": "#FFFDE7",   # Light Yellow
    "REMOTE_BRIDGE": "#F3E5F5", # Light Purple
    "REMOTE_RESOURCE": "#F5F5F5",# Light Gray
    "CYCLE": "#FFCDD2",         # Light Red
    "BORDER": "#B0BEC5",
    "TEXT": "#37474F"
}

class NodeSocket(QGraphicsItem):
    def __init__(self, parent, socket_type, index, is_output=False):
        super().__init__(parent)
        self.parent_node = parent
        self.socket_type = socket_type
        self.index = index
        self.is_output = is_output
        self.radius = 5.0 # Slightly smaller
        self.edges = []
        
        # Color coding by data type (Simplified heuristic)
        # Image=Blue, Number=Yellow, String=Gray, Default=Green/Cyan
        st = str(socket_type).lower()
        if any(x in st for x in ['image', 'img', 'mat', 'frame']):
            self.color = QColor("#4FC3F7") # Light Blue
        elif any(x in st for x in ['int', 'float', 'number', 'threshold', 'size']):
            self.color = QColor("#FFF176") # Yellow
        elif any(x in st for x in ['str', 'text', 'file', 'path']):
            self.color = QColor("#BDBDBD") # Gray
        else:
            self.color = QColor("#A5D6A7") if not is_output else QColor("#80DEEA")

        self.setAcceptHoverEvents(True)
        self.setToolTip(f"{socket_type} ({'Output' if is_output else 'Input'})")
        
    def boundingRect(self):
        return QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
        
    def paint(self, painter, option, widget):
        try:
            transform = painter.worldTransform()
            # Fix for 'QTransform' object has no attribute 'isSingular'
            # Use determinant check instead
            try:
                if transform.determinant() == 0:
                    return
            except AttributeError:
                pass # If determinant also fails, we proceed (risk of error later but unlikely)
                
            scale = option.levelOfDetailFromTransform(transform)
            if math.isnan(scale) or math.isinf(scale) or scale < 0.01: 
                return

            painter.setBrush(QBrush(self.color))
            # No Pen for clean look, or thin pen
            painter.setPen(QPen(QColor("#455A64"), 1))
            painter.drawEllipse(QPointF(0,0), self.radius, self.radius)
        except Exception as e:
            logger.error(f"NodeSocket paint error: {e}")

    def get_scene_pos(self):
        return self.scenePos()

class NodeItem(QGraphicsItem):
    def __init__(self, title="Node", inputs=[], outputs=[], node_type="Function"):
        super().__init__()
        self.title = title
        self.inputs = inputs
        self.outputs = outputs
        self.node_type = node_type
        self.params = {}
        self.width = 220
        self.height = 100
        self.locked = False  # Principle 5: User Locking
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges) # Important for detecting moves
        self.setAcceptHoverEvents(True)
        
        self._init_sockets()
        self._update_colors()

    def _init_sockets(self):
        self.input_sockets = []
        self.output_sockets = []
        
        # Calculate height based on sockets
        socket_height = max(len(self.inputs), len(self.outputs)) * 20
        self.height = max(80, 40 + socket_height)

        for i, inp in enumerate(self.inputs):
            s = NodeSocket(self, inp, i, is_output=False)
            y = 30 + i * 20 + 10
            s.setPos(0, y)
            self.input_sockets.append(s)
            
        for i, out in enumerate(self.outputs):
            s = NodeSocket(self, out, i, is_output=True)
            y = 30 + i * 20 + 10
            s.setPos(self.width, y)
            self.output_sockets.append(s)

    def _update_colors(self):
        # Determine Color Scheme
        theme = options_manager.settings.get("theme", "Nord")
        
        if theme == "Tactical":
            # GFL Style: Dark, Tech, Yellow accents
            self.base_color = QColor("#212121")   # Panel BG
            self.header_color = QColor("#1A1A1A") # Darker Header
            self.text_color = QColor("#E0E0E0")
            self.sub_text_color = QColor("#9E9E9E")
            
            # Type specific border/accents
            nt = self.node_type.lower()
            if "project" in nt: self.border_color = QColor("#FDC800") # Gold
            elif "module" in nt: self.border_color = QColor("#00E5FF") # Cyan
            elif "class" in nt: self.border_color = QColor("#76FF03") # Lime
            elif "function" in nt: self.border_color = QColor("#FF4081") # Pink
            else: self.border_color = QColor("#FDC800")
            
        elif theme == "Light":
            # Clean Light Theme
            self.base_color = QColor("#FFFFFF")
            self.header_color = QColor("#F5F5F5")
            self.border_color = QColor("#E0E0E0")
            self.text_color = QColor("#212121")
            self.sub_text_color = QColor("#757575")
            
        else: # Nord / Dark Default
            self.base_color = QColor(COLORS["body"])
            self.header_color = QColor(COLORS["background"])
            self.border_color = QColor(COLORS["border"])
            self.text_color = QColor(COLORS["text"])
            self.sub_text_color = QColor(COLORS["text_dim"])

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Principle 5: Dragging locks the node
            # But wait, ItemPositionHasChanged is also called during auto-layout.
            # We need to distinguish user drag vs code setPos.
            # Usually, if scene().mouseGrabberItem() is this item, it's a drag.
            scene = self.scene()
            if scene and scene.mouseGrabberItem() == self:
                self.locked = True
                self.update() # Repaint to show lock status
                
        return super().itemChange(change, value)

    def paint(self, painter, option, widget):
        # ... (Existing Paint Logic) ...
        # Simplified for brevity, need to merge with existing
        # I will include the existing logic but add the "Locked" indicator
        
        theme = options_manager.settings.get("theme", "Nord")
        is_tactical = (theme == "Tactical")
        
        # LOD
        transform = painter.worldTransform()
        scale = option.levelOfDetailFromTransform(transform)
        if scale < 0.2:
            # Low LOD: Just a rect
            painter.setBrush(QBrush(self.base_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(self.boundingRect())
            return

        # Body
        path = QPainterPath()
        radius = 0 if is_tactical else 8
        path.addRoundedRect(0, 0, self.width, self.height, radius, radius)
        
        painter.setBrush(QBrush(self.base_color))
        
        # Selection / Lock Highlight
        pen_width = 1.5
        border_col = self.border_color
        
        if self.isSelected():
            border_col = QColor("#88C0D0") # Nord Blue
            if is_tactical: border_col = QColor("#FDC800") # Yellow
            pen_width = 2.5
            
        if self.locked:
            # Principle 5: Visual indicator for locked nodes
            # Maybe a dashed border or a lock icon?
            # Let's use a subtle visual cue, e.g. a different border style or icon
            pass # We will draw icon later

        painter.setPen(QPen(border_col, pen_width))
        painter.drawPath(path)
        
        # Header
        path_header = QPainterPath()
        path_header.setFillRule(Qt.FillRule.WindingFill)
        path_header.addRoundedRect(0, 0, self.width, 28, radius, radius)
        if not is_tactical:
            # Clip bottom corners for rounded look on top only
            path_header.addRect(0, 20, self.width, 8) 
        
        painter.save()
        painter.setClipPath(path)
        painter.fillPath(path_header, QBrush(self.header_color))
        painter.restore()

        # For Tactical, add a bottom line to header
        if is_tactical:
            painter.setPen(QPen(QColor("#333"), 1))
            painter.drawLine(0, 28, self.width, 28)

        # Locked Icon (Top Right or Left)
        if self.locked:
            painter.setPen(QColor("#FF5252") if not is_tactical else QColor("#FDC800"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(self.width - 20, -15, 20, 15), Qt.AlignmentFlag.AlignCenter, "🔒")

        # Header Text (Title)
        title_color = self.text_color
        painter.setPen(title_color)
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        painter.drawText(QRectF(10, 0, self.width-40, 28), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.title)
        
        # Middle Section (Subtitle)
        if scale > 0.4:
            subtitle = self.params.get("func_name", "")
            painter.setPen(self.sub_text_color)
            painter.setFont(QFont("Segoe UI", 8))
            rect = QRectF(10, 35, self.width-20, self.height-40)
            painter.drawText(rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, subtitle)
        
        # Socket Labels
        if scale > 0.6:
            painter.setPen(self.sub_text_color)
            painter.setFont(QFont("Segoe UI", 8))
            
            # Inputs
            for i, inp in enumerate(self.inputs):
                y = 30 + i * 20 + 10
                painter.drawText(QRectF(10, y-10, self.width/2, 20), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, inp)
                
            # Outputs
            for i, out in enumerate(self.outputs):
                y = 30 + i * 20 + 10
                painter.drawText(QRectF(self.width/2, y-10, self.width/2-10, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, out)

    def hoverEnterEvent(self, event):
        # Highlight connected edges
        for socket in self.input_sockets + self.output_sockets:
            for edge in socket.edges:
                edge.set_highlight(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        # Un-highlight connected edges
        for socket in self.input_sockets + self.output_sockets:
            for edge in socket.edges:
                edge.set_highlight(False)
        super().hoverLeaveEvent(event)

    def contextMenuEvent(self, event):
        menu = QMenu()
        
        # Principle 5: Unlock Single Node
        if self.locked:
            action_unlock = menu.addAction("Unlock Node")
            action_unlock.triggered.connect(lambda: self.unlock_self())
            
        # Standard Actions
        # action_delete = menu.addAction("Delete Node") # Future
        
        if not menu.isEmpty():
            menu.exec(event.screenPos())

    def unlock_self(self):
        scene = self.scene()
        if scene and hasattr(scene, "unlock_node"):
            scene.unlock_node(self)
        else:
            self.locked = False
            self.update()

class NodeEdge(QGraphicsPathItem):
    def __init__(self, source_socket, target_socket=None, target_point=None, weight=1, edge_type="call", risk="low", status="unchanged"):
        super().__init__()
        self.source_socket = source_socket
        self.target_socket = target_socket
        self.target_point = target_point
        self.weight = weight
        self.edge_type = edge_type
        self.risk = risk
        self.status = status 
        self.highlighted = False
        
        self.setZValue(-1)
        self.update_path()
        try:
            if self.source_socket and hasattr(self.source_socket, "edges"):
                self.source_socket.edges.append(self)
            if self.target_socket and hasattr(self.target_socket, "edges"):
                self.target_socket.edges.append(self)
        except Exception:
            pass
            
    def set_highlight(self, val):
        self.highlighted = val
        self.update_path()
        self.update() # Ensure repaint
        
    def update_path(self):
        if not self.source_socket: return
        try:
            # Safety check
            if not self.source_socket.scene(): return
                
            p1 = self.source_socket.get_scene_pos()
            if self.target_socket:
                if not self.target_socket.scene(): return
                p2 = self.target_socket.get_scene_pos()
            elif self.target_point:
                p2 = self.target_point
            else:
                return
            
            if (math.isnan(p1.x()) or math.isnan(p1.y()) or 
                math.isnan(p2.x()) or math.isnan(p2.y())):
                return

            # Principle 3: Orthogonal Lines Only (Manhattan)
            # "Stream" style: Left -> Right
            
            path = QPainterPath(p1)
            
            # Simple Orthogonal: Horizontal -> Vertical -> Horizontal
            mid_x = (p1.x() + p2.x()) / 2
            
            # Adjust if backward flow
            if p2.x() < p1.x() + 20: 
                # Go around
                mid_x = p1.x() + 50 
                mid_y = p1.y() + (p2.y() - p1.y()) / 2
                
                # Path: Right -> Up/Down -> Left -> Up/Down -> Right
                path.lineTo(mid_x, p1.y())
                
                # If very close vertically, might overlap
                path.lineTo(mid_x, p2.y()) # This is actually just L-shape if mid_x > p2.x
                # Wait, if p2.x < p1.x, mid_x (p1+50) is > p1.x and > p2.x
                # So: p1 -> (mid_x, p1.y) -> (mid_x, p2.y) -> p2
                path.lineTo(p2)
            else:
                # Forward flow
                path.lineTo(mid_x, p1.y())
                path.lineTo(mid_x, p2.y())
                path.lineTo(p2)
            
            self.setPath(path)
            
        except Exception as e:
            logger.error(f"NodeEdge update_path error: {e}")
            
    def paint(self, painter, option, widget=None):
        # Principle 3: Minimalist, No Arrows, Gap on Crossing
        
        path = self.path()
        if path.isEmpty(): return

        # Theme
        theme = options_manager.settings.get("theme", "Nord")
        is_tactical = (theme == "Tactical")
        
        # Colors
        color = QColor("#B0BEC5") # Default Gray
        if is_tactical: color = QColor("#666")
        
        width = 1.5 # Thin line (Principle 3)
        
        if self.highlighted:
            color = QColor("#29B6F6")
            if is_tactical: color = QColor("#FDC800")
            width = 2.5
        
        # 1. Draw "Gap" Mask (Thick Background Line)
        # This creates the hollow effect when crossing other lines (assuming Z-order works)
        # Background color matches the canvas background
        bg_color = QColor("#2E3440") # Nord BG
        if is_tactical: bg_color = QColor("#1A1A1A") # Tactical BG
        if theme == "Light": bg_color = QColor("#FFFFFF")
        
        pen_mask = QPen(bg_color, width + 4) # Wider than actual line
        painter.setPen(pen_mask)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)
        
        # 2. Draw Actual Line
        pen = QPen(color, width)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # No Arrows (Principle 3)
