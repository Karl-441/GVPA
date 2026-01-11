from PyQt6.QtWidgets import (QGraphicsItem, QGraphicsPathItem, QGraphicsTextItem, 
                             QGraphicsProxyWidget, QWidget, QVBoxLayout, QLabel, 
                             QLineEdit, QPushButton)
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
        self.title = str(title) 
        self.node_type = node_type
        self.width = 220 # Fixed min width
        self.subtitle = "" # Will store core params string
        self.value_text = ""
        self.custom_style = {}
        self.exec_seq = 0
        
        # Truncate lists
        display_inputs = inputs[:10] + ["..."] if len(inputs) > 10 else inputs
        display_outputs = outputs[:10] + ["..."] if len(outputs) > 10 else outputs
             
        # Fixed Height partitions? Or dynamic?
        # Header (Type) + Body (Core) + Footer (Status)?
        # Actually Left-Middle-Right logic is better drawn than strictly layouted.
        # But we need height to accommodate sockets.
        self.height = 60 + max(len(display_inputs), len(display_outputs)) * 20
        
        self.inputs = [str(i) for i in display_inputs] 
        self.outputs = [str(o) for o in display_outputs]
        self.input_sockets = []
        self.output_sockets = []
        self.params = {} 
        
        self.base_color = QColor("#FFFFFF")
        self.header_color = QColor("#ECEFF1")
        self.text_color = QColor("#37474F")
        self.sub_text_color = QColor("#546E7A")
        self._update_colors()
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges) 
        self.setAcceptHoverEvents(True)
        
        # Optimization: Cache the node rendering
        # This significantly improves performance when dragging/scrolling
        self.setCacheMode(QGraphicsItem.CacheMode.DeviceCoordinateCache)
        
        # Create sockets - Left Side (Inputs)
        # Sort Inputs: We assume they are passed in order. 
        # But user asked: "Input Socket sorted by topology priority (Bottom-up?)"
        # For now keep simple list order, but position them carefully.
        
        start_y = 30 # Below header
        
        for i, inp in enumerate(self.inputs):
            socket = NodeSocket(self, inp, i, is_output=False)
            socket.setPos(-5, start_y + i * 20 + 10) # Left edge
            self.input_sockets.append(socket)
            
        for i, out in enumerate(self.outputs):
            socket = NodeSocket(self, out, i, is_output=True)
            socket.setPos(self.width + 5, start_y + i * 20 + 10) # Right edge
            self.output_sockets.append(socket)

    def set_params(self, params):
        self.params = params
        self.exec_seq = params.get("_exec_seq", 0)
        
        # Extract Core Info for Middle Section
        # For OpenCV: file path, threshold
        # For Function: func_name
        core_info = []
        if "file" in params and params["file"]:
            core_info.append(os.path.basename(params["file"]))
        
        # Add specific known params if exist
        for k in ["threshold", "ksize", "alpha", "beta"]:
            if k in params:
                core_info.append(f"{k}:{params[k]}")
                
        self.subtitle = "\n".join(core_info[:3]) # Max 3 lines
        
        # Adjust width if needed
        font = QFont("Segoe UI", 9)
        fm = QFontMetrics(font)
        text_w = fm.horizontalAdvance(self.title)
        self.width = max(220, min(text_w + 100, 350))
        
        # Re-position output sockets if width changed
        start_y = 30
        for i, socket in enumerate(self.output_sockets):
            socket.setPos(self.width + 5, start_y + i * 20 + 10)

        self._update_colors()
        self._update_tooltip()

    def set_style(self, style):
        self.custom_style = style
        self._update_colors()
        self.update()

    def _update_colors(self):
        # Determine Color Scheme
        theme = options_manager.settings.get("theme", "Nord")
        
        if theme == "Tactical":
            # GFL Style: Dark, Tech, Yellow accents
            self.base_color = QColor("#212121")   # Panel BG
            self.header_color = QColor("#1A1A1A") # Darker Header
            self.text_color = QColor("#E0E0E0")
            self.sub_text_color = QColor("#9E9E9E")
            
            # Type indicators can use colored borders or small accents in paint
            # But header color is unified dark for clean look
            # Or use subtle tint
            nt = self.node_type.lower()
            if any(x in nt for x in ["read", "input", "save", "output", "show"]):
                 self.header_color = QColor("#1A1A1A") # Keep consistent
            elif any(x in nt for x in ["canny", "blur", "convert", "cv2"]):
                 self.header_color = QColor("#1A1A1A")
            
            # Use custom style color if present as a subtle tint or border
            if self.custom_style and "color" in self.custom_style:
                 # In Tactical, maybe just border color changes? 
                 # Or header background slightly tinted?
                 try:
                    c = QColor(self.custom_style["color"])
                    if c.isValid():
                        self.header_color = QColor("#2A2A2A") # Slightly lighter
                 except:
                    pass

        elif theme == "Dark":
            self.base_color = QColor("#424242")
            self.header_color = QColor("#616161")
            self.text_color = QColor("#F5F5F5")
            self.sub_text_color = QColor("#BDBDBD")
            
            # Adjust header colors for types (Darker variants)
            nt = self.node_type.lower()
            if any(x in nt for x in ["read", "input", "save", "output", "show"]):
                self.header_color = QColor("#1565C0") # Blue 800
            elif any(x in nt for x in ["canny", "blur", "convert", "cv2"]):
                self.header_color = QColor("#00838F") # Cyan 800
            elif "function" in nt:
                self.header_color = QColor("#2E7D32") # Green 800
            elif "file" in nt:
                self.header_color = QColor("#1565C0")
            elif "module" in nt:
                self.header_color = QColor("#00695C") # Teal 800
            elif "class" in nt:
                self.header_color = QColor("#6A1B9A") # Purple 800
                
        else:
            # Light / Nord (Default Light Nodes on Dark BG)
            self.base_color = QColor("#FFFFFF") # Default White
            self.header_color = QColor("#ECEFF1")
            self.text_color = QColor("#37474F")
            self.sub_text_color = QColor("#546E7A")
            
            nt = self.node_type.lower()
            if any(x in nt for x in ["read", "input", "save", "output", "show"]):
                self.base_color = QColor("#E3F2FD") # Light Blue
                self.header_color = QColor("#BBDEFB")
            elif any(x in nt for x in ["canny", "blur", "convert", "cv2"]):
                self.base_color = QColor("#E0F7FA") # Cyan
                self.header_color = QColor("#B2EBF2")
            elif "function" in nt:
                self.base_color = QColor("#E8F5E9") # Light Green
                self.header_color = QColor("#C8E6C9")
            elif "file" in nt:
                self.base_color = QColor("#E3F2FD") # Blue-ish White
                self.header_color = QColor("#90CAF9") # Blue 200
            elif "module" in nt:
                self.base_color = QColor("#E0F2F1") # Teal-ish White
                self.header_color = QColor("#80CBC4") # Teal 200
            elif "class" in nt:
                self.base_color = QColor("#F3E5F5") # Purple-ish White
                self.header_color = QColor("#CE93D8") # Purple 200
        
        # Apply Custom Style (Layer Colors) - skip for Tactical to maintain look
        if theme != "Tactical" and self.custom_style:
            if "color" in self.custom_style:
                try:
                    c = QColor(self.custom_style["color"])
                    if c.isValid():
                        self.base_color = c
                        self.header_color = c.darker(110)
                except Exception:
                    pass

        # Dead Code Override
        is_dead = self.params.get("_is_dead", False)
        if is_dead:
            if theme == "Tactical":
                self.base_color = QColor("#111")
                self.header_color = QColor("#222")
                self.text_color = QColor("#444")
            else:
                self.base_color = QColor("#F5F5F5") if theme != "Dark" else QColor("#212121")
                self.header_color = QColor("#E0E0E0") if theme != "Dark" else QColor("#424242")
                self.text_color = QColor("#9E9E9E")

    def _update_tooltip(self):
        tooltip = f"<b>{self.title}</b><br>Type: {self.node_type}"
        if self.exec_seq > 0:
            tooltip += f"<br>Exec Order: #{self.exec_seq}"
        if self.params:
            tooltip += "<hr><b>Params:</b><br>"
            for k, v in self.params.items():
                if not k.startswith("_"):
                    tooltip += f"{k}: {v}<br>"
        self.setToolTip(tooltip)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            grid_size = 20
            x = round(new_pos.x() / grid_size) * grid_size
            y = round(new_pos.y() / grid_size) * grid_size
            return QPointF(x, y)
            
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            # Update connected edges
            for socket in self.input_sockets + self.output_sockets:
                for edge in socket.edges:
                    edge.update_path()
                    
        return super().itemChange(change, value)

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

    def boundingRect(self):
        return QRectF(-10, -10, self.width + 20, self.height + 20)
        
    def paint(self, painter, option, widget):
        try:
            transform = painter.worldTransform()
            try:
                if transform.determinant() == 0:
                    return
            except AttributeError:
                pass
                
            scale = option.levelOfDetailFromTransform(transform)
            if math.isnan(scale) or math.isinf(scale) or scale < 0.01: 
                return # Optimization

            theme = options_manager.settings.get("theme", "Nord")
            is_tactical = (theme == "Tactical")
            radius = 0 if is_tactical else 8 # Sharp corners for Tactical

            # --- 1. Background & Shape ---
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width, self.height, radius, radius)
            
            # Draw Background
            painter.setBrush(QBrush(self.base_color))
            
            # Border
            status = self.params.get("_status", "unchanged")
            border_color = QColor("#90A4AE") # Default Gray-Blue
            border_width = 1
            
            if is_tactical:
                 border_color = QColor("#555") # Darker border default
            
            if self.isSelected():
                border_color = QColor("#FDC800") if is_tactical else QColor("#2196F3")
                border_width = 2
            elif status == "added":
                border_color = QColor("#4CAF50")
                border_width = 2
            elif status == "removed":
                border_color = QColor("#F44336")
                border_width = 2
                
            is_dead = self.params.get("_is_dead", False)
            if is_dead:
                border_color = QColor("#BDBDBD") if not is_tactical else QColor("#333")
                
            painter.setPen(QPen(border_color, border_width))
            painter.drawPath(path)
            
            # --- 2. Sections ---
            # Header
            
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(self.header_color))
            # Header rounding top only
            path_header = QPainterPath()
            path_header.addRoundedRect(0, 0, self.width, 28, radius, radius)
            # Clip bottom of header to be straight
            painter.save()
            painter.setClipRect(0, 0, self.width, 28)
            painter.drawPath(path_header)
            painter.restore()

            # For Tactical, add a bottom line to header
            if is_tactical:
                painter.setPen(QPen(QColor("#333"), 1))
                painter.drawLine(0, 28, self.width, 28)

            # Exec Seq Badge
            if self.exec_seq > 0:
                badge_bg = QColor("#FDC800") if is_tactical else QColor("#546E7A")
                badge_fg = QColor("black") if is_tactical else QColor("white")
                
                painter.setBrush(QBrush(badge_bg))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(-8, -8, 20, 20)
                painter.setPen(badge_fg)
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                painter.drawText(QRectF(-8, -8, 20, 20), Qt.AlignmentFlag.AlignCenter, str(self.exec_seq))

            # Header Text (Title)
            title_color = QColor("#F0F0F0") if is_tactical else QColor("#37474F")
            if theme == "Dark": title_color = QColor("#F5F5F5")
            
            painter.setPen(title_color)
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(QRectF(30, 0, self.width-60, 28), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.title)
            
            # Right Header Icon
            nt = self.node_type.lower()
            icon_char = "</>"
            if "cv2" in nt or "image" in nt:
                icon_char = "[O]"
            elif "file" in nt:
                icon_char = "[F]"
            elif "module" in nt:
                icon_char = "[M]"
            elif "class" in nt:
                icon_char = "[C]"
            painter.setFont(QFont("Consolas", 9))
            painter.drawText(QRectF(self.width-30, 0, 25, 28), Qt.AlignmentFlag.AlignCenter, icon_char)
            
            # Middle Section
            if scale > 0.4:
                painter.setPen(self.sub_text_color)
                painter.setFont(QFont("Segoe UI", 8))
                rect = QRectF(10, 35, self.width-20, self.height-40)
                painter.drawText(rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, self.subtitle)
            
            # Status Section
            hits = self.params.get("_hits", 0)
            if hits > 0 or is_dead:
                hit_color = "#4CAF50" if hits > 0 else "#BDBDBD"
                if is_tactical and hits > 0: hit_color = "#FDC800"
                if is_tactical and is_dead: hit_color = "#444"
                
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(hit_color)))
                painter.drawRoundedRect(self.width-40, self.height-20, 35, 16, radius, radius)
                painter.setPen(QColor("white") if not is_tactical else QColor("black"))
                painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                painter.drawText(QRectF(self.width-40, self.height-20, 35, 16), Qt.AlignmentFlag.AlignCenter, f"{hits}x")

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

        except Exception as e:
            logger.error(f"NodeItem paint error: {e}")

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
        self.update_path() # Redraw with new style
        
    def update_path(self):
        if not self.source_socket: return
        try:
            # Safety check: Socket must be in a scene to get a valid scene position
            if not self.source_socket.scene():
                return
                
            p1 = self.source_socket.get_scene_pos()
            if self.target_socket:
                if not self.target_socket.scene():
                    return
                p2 = self.target_socket.get_scene_pos()
            elif self.target_point:
                p2 = self.target_point
            else:
                return
            
            # NaN/Inf check
            if (math.isnan(p1.x()) or math.isnan(p1.y()) or 
                math.isnan(p2.x()) or math.isnan(p2.y())):
                return

            # --- Orthogonal Path Finding (Manhattan Routing) ---
            path = QPainterPath(p1)
            
            mid_x = (p1.x() + p2.x()) / 2
            
            # Adjust mid_x if nodes are close or reversed
            if p2.x() < p1.x() + 20: # Backward or close vertical
                mid_x = p1.x() + 50 # Go out further right
                
                path = QPainterPath(p1)
                ctrl1 = QPointF(p1.x() + 100, p1.y())
                ctrl2 = QPointF(p2.x() - 100, p2.y())
                path.cubicTo(ctrl1, ctrl2, p2)
            else:
                # Standard Forward Orthogonal
                path.lineTo(mid_x, p1.y())
                path.lineTo(mid_x, p2.y())
                path.lineTo(p2)
            
            self.setPath(path)
            
            # Style
            width = 2
            color = QColor("#B0BEC5") # Default Gray
            style = Qt.PenStyle.SolidLine
            
            theme = options_manager.settings.get("theme", "Nord")
            is_tactical = (theme == "Tactical")

            if is_tactical:
                color = QColor("#666")
                
            if self.highlighted:
                width = 3
                color = QColor("#29B6F6") # Highlight Blue
                if is_tactical:
                    color = QColor("#FDC800")
            
            # Status Override
            if self.status == "added":
                color = QColor("#66BB6A")
            elif self.status == "removed":
                color = QColor("#EF5350")
                style = Qt.PenStyle.DashLine
                
            if self.edge_type == "cycle":
                color = QColor("#FF5252")
                width = 3
            
            pen = QPen(color, width)
            pen.setStyle(style)
            self.setPen(pen)
            
            # Optimization: Pre-calculate arrow polygon
            self.arrow_poly = None
            if path.length() > 5:
                p_end = path.currentPosition()
                p_pre = path.pointAtPercent(0.99)
                angle = math.atan2(p_end.y() - p_pre.y(), p_end.x() - p_pre.x())
                
                size = 8
                p1 = p_end
                p2 = QPointF(p_end.x() - size * math.cos(angle - 0.5), 
                             p_end.y() - size * math.sin(angle - 0.5))
                p3 = QPointF(p_end.x() - size * math.cos(angle + 0.5), 
                             p_end.y() - size * math.sin(angle + 0.5))
                
                poly = QPainterPath()
                poly.moveTo(p1)
                poly.lineTo(p2)
                poly.lineTo(p3)
                poly.closeSubpath()
                self.arrow_poly = poly
            
        except Exception as e:
            logger.error(f"NodeEdge update_path error: {e}")
            
    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        # Optimization: Use pre-calculated arrow polygon
        try:
            if hasattr(self, 'arrow_poly') and self.arrow_poly:
                painter.setBrush(self.pen().color())
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPath(self.arrow_poly)
        except Exception as e:
            logger.error(f"NodeEdge paint error: {e}")
