from PyQt6.QtWidgets import (QGraphicsScene, QGraphicsView, QWidget, QVBoxLayout, 
                             QMenu, QApplication, QInputDialog, QGraphicsItem)
from PyQt6.QtCore import Qt, QPoint, QLineF, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QTransform, QDrag, QFont
from interface.gui.components.node_graph_items import NodeItem, NodeEdge, NodeSocket, COLORS
from engine.nodes.opencv_nodes import NodeRegistry
import json
import os
from utils.logger import logger
from core.options_manager import options_manager

class NodeGraphScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QColor(COLORS["background"]))
        # Dynamic scene rect - start with a large area but not fixed forever
        # Ideally, we want the scene rect to be "infinite". 
        # Setting a very large rect is the standard way in QGraphicsScene.
        # But to allow scrolling further, we can update it when items move.
        self.setSceneRect(-1000000, -1000000, 2000000, 2000000) 
        self.nodes = []
        self.edges = []
        self._base_rect = QRectF(-1000000, -1000000, 2000000, 2000000)
        self.collapsed_modules = set()
        
    def add_node(self, node):
        self.addItem(node)
        self.nodes.append(node)
        # self.update_scene_rect() # Optional: if we want tight bounding
        return node
    
    def apply_options(self, options: dict):
        theme = options.get("theme", "Nord")
        if theme == "Light":
            self.setBackgroundBrush(QColor("#FFFFFF"))
        elif theme == "Dark":
            self.setBackgroundBrush(QColor("#1E1E1E"))
        elif theme == "Tactical":
            self.setBackgroundBrush(QColor("#1A1A1A")) # Dark tactical background
        else:
            self.setBackgroundBrush(QColor(COLORS["background"]))
        
        # Update all nodes to match theme
        for node in self.nodes:
            if hasattr(node, "_update_colors"):
                node._update_colors()
                node.update()

        infinite = options.get("infinite_canvas", True)
        if infinite:
            self.setSceneRect(self._base_rect)
        else:
            # Tight bounding around items
            rect = self.itemsBoundingRect().adjusted(-200, -200, 200, 200)
            self.setSceneRect(rect)
        
    def add_edge(self, source, target, weight=1):
        edge = NodeEdge(source, target, weight=weight)
        self.addItem(edge)
        self.edges.append(edge)
        return edge
    
    def collapse_module_for_node(self, node):
        mod = node.params.get("module", "")
        if not mod: return
        self.collapsed_modules.add(mod)
        for n in self.nodes:
            if n is not node and n.params.get("module", "") == mod and n.node_type != "Module":
                n.setVisible(False)
        for e in self.edges:
            if not e.source_socket.parent_node.isVisible() or not e.target_socket.parent_node.isVisible():
                e.setVisible(False)
    
    def expand_module_for_node(self, node):
        mod = node.params.get("module", "")
        if not mod: return
        if mod in self.collapsed_modules:
            self.collapsed_modules.remove(mod)
        for n in self.nodes:
            if n.params.get("module", "") == mod:
                n.setVisible(True)
        for e in self.edges:
            e.setVisible(True)

    def remove_edge(self, edge):
        self.removeItem(edge)
        if edge in self.edges:
            self.edges.remove(edge)
        
        # Cleanup socket references
        if edge.source_socket and hasattr(edge.source_socket, "edges") and edge in edge.source_socket.edges:
            edge.source_socket.edges.remove(edge)
        if edge.target_socket and hasattr(edge.target_socket, "edges") and edge in edge.target_socket.edges:
            edge.target_socket.edges.remove(edge)

    def serialize(self):
        data = {"nodes": [], "edges": []}
        for i, node in enumerate(self.nodes):
            node_data = {
                "id": i,
                "title": node.title,
                "x": node.pos().x(),
                "y": node.pos().y(),
                "inputs": node.inputs,
                "outputs": node.outputs,
                "params": node.params if hasattr(node, "params") else {}
            }
            node._temp_id = i
            data["nodes"].append(node_data)
            
        for edge in self.edges:
            source_node = edge.source_socket.parent_node
            target_node = edge.target_socket.parent_node
            edge_data = {
                "source": source_node._temp_id,
                "source_socket": edge.source_socket.index,
                "target": target_node._temp_id,
                "target_socket": edge.target_socket.index,
                "weight": getattr(edge, "weight", 1)
            }
            data["edges"].append(edge_data)
            
        return data

    def clear_graph(self):
        """
        Optimized graph clearing.
        Uses native QGraphicsScene.clear() for performance, then resets Python state.
        """
        # 1. Clear internal Python references immediately
        # Breaking these lists releases the Python objects (if no other refs exist)
        self.nodes.clear()
        self.edges.clear()
        self.collapsed_modules.clear()
        
        # 2. Native Clear (Fastest C++ implementation)
        # Removes all items from the BSP tree and deletes them
        self.clear()
    
    def unlock_all_nodes(self):
        """Principle 5: Batch Unlock"""
        for node in self.nodes:
            if hasattr(node, "locked"):
                node.locked = False
                node.update()
        logger.info("All nodes unlocked by user.")

    def unlock_node(self, node):
        """Principle 5: Unlock Single Node"""
        if hasattr(node, "locked"):
            node.locked = False
            node.update()
            logger.info(f"Node {node.title} unlocked.")


    def deserialize(self, data):
        self.clear_graph()
        # self.nodes = [] # Already cleared
        # self.edges = [] # Already cleared
        
        node_map = {} 
        
        for n_data in data.get("nodes", []):
            node_type = n_data.get("type", "Function")
            node = NodeItem(n_data["title"], n_data["inputs"], n_data["outputs"], node_type=node_type)
            node.setPos(n_data["x"], n_data["y"])
            # Use set_params to ensure tooltip update
            node.set_params(n_data.get("params", {}))
            if "style" in n_data:
                node.set_style(n_data["style"])
            self.add_node(node)
            node_map[n_data["id"]] = node
            
        for e_data in data.get("edges", []):
            source = node_map.get(e_data["source"])
            target = node_map.get(e_data["target"])
            if source and target:
                try:
                    source_socket = source.output_sockets[e_data["source_socket"]]
                    target_socket = target.input_sockets[e_data["target_socket"]]
                    weight = e_data.get("weight", 1)
                    edge_type = e_data.get("type", "call")
                    risk = e_data.get("risk", "low")
                    status = e_data.get("_status", "unchanged")
                    
                    edge = NodeEdge(source_socket, target_socket, weight=weight, edge_type=edge_type, risk=risk, status=status)
                    self.addItem(edge)
                    self.edges.append(edge)
                except IndexError:
                    logger.warning("Socket index out of range during deserialization")
        
        self.update()

class NodeGraphWidget(QGraphicsView):
    node_selected = pyqtSignal(str, int) # Signal: file_path, lineno

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = NodeGraphScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        # Optimization: Use SmartViewportUpdate for better performance
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)
        self.setAcceptDrops(True)
        # Optimization: Cache background for faster redraws
        self.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)
        self.setOptimizationFlag(QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing, True)

        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.temp_edge = None
        self.start_socket = None
        
        # Connect selection change
        self.scene.selectionChanged.connect(self.on_selection_changed)
    
    def apply_options(self, options: dict):
        try:
            self.scene.apply_options(options)
            self.viewport().update()
        except Exception as e:
            logger.error(f"Apply options failed: {e}")

    def drawForeground(self, painter, rect):
        # Draw Instructions Overlay
        painter.save()
        painter.setTransform(QTransform()) # Reset transform to draw in window coordinates
        
        # Principle 8: Empty Canvas Hint
        if not self.scene.nodes:
            painter.setPen(QColor(COLORS["text_dim"]))
            painter.setFont(QFont("Segoe UI", 14))
            viewport_rect = self.viewport().rect()
            painter.drawText(viewport_rect, Qt.AlignmentFlag.AlignCenter, "Empty Canvas - Right Click to Add Node")
        
        instruction = "Mouse Wheel: Zoom | Middle/Left Drag: Pan | Right Click: Edit Params"
        
        painter.setPen(QColor(COLORS["text_dim"]))
        painter.setFont(QFont("Segoe UI", 9))
        
        # Draw at bottom left
        viewport_rect = self.viewport().rect()
        text_rect = QRectF(10, viewport_rect.height() - 30, viewport_rect.width()-20, 20)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, instruction)
        
        # Minimap (Experimental & Optimized)
        try:
            # Optimization: Fast exit if disabled
            if not options_manager.settings.get("show_minimap", False):
                painter.restore()
                return

            # Draw minimap rect at bottom right
            map_size = 200
            viewport_rect = self.viewport().rect()
            map_rect = QRectF(viewport_rect.width() - map_size - 10, 
                              viewport_rect.height() - map_size - 10, 
                              map_size, map_size)
             
            # Draw Background
            painter.setBrush(QColor(0, 0, 0, 100))
            painter.setPen(QColor(255, 255, 255, 50))
            painter.drawRect(map_rect)
             
            # Optimization: Skip content drawing if dragging/panning to maintain high FPS
            if self.dragMode() == QGraphicsView.DragMode.ScrollHandDrag and self.viewport().cursor().shape() == Qt.CursorShape.ClosedHandCursor:
                 # Just draw border when dragging fast
                 pass
            else:
                 # Draw Scene Content
                 # Optimization: Use scene itemsBoundingRect only if cached or needed? 
                 # itemsBoundingRect is potentially slow (iterates all items).
                 # Use self.scene.sceneRect() if it's maintained well, or self.scene.itemsBoundingRect() carefully.
                 scene_rect = self.scene.itemsBoundingRect()
                 
                 if scene_rect.width() > 0 and scene_rect.height() > 0:
                     scale_x = map_size / max(scene_rect.width(), 1)
                     scale_y = map_size / max(scene_rect.height(), 1)
                     scale = min(scale_x, scale_y) * 0.9
                     
                     # Draw nodes as dots
                     # Optimization: Batch draw calls? Or use points?
                     painter.setBrush(QColor(200, 200, 200, 150))
                     painter.setPen(Qt.PenStyle.NoPen)
                     
                     # Limit node drawing count for performance on massive graphs
                     node_limit = 500
                     count = 0
                     for node in self.scene.nodes:
                         if count > node_limit: break # Cap rendering
                         if not node.isVisible(): continue
                         
                         # Map node pos to map rect
                         rel_x = (node.pos().x() - scene_rect.x()) * scale
                         rel_y = (node.pos().y() - scene_rect.y()) * scale
                         
                         draw_x = map_rect.left() + rel_x + (map_size - scene_rect.width()*scale)/2
                         draw_y = map_rect.top() + rel_y + (map_size - scene_rect.height()*scale)/2
                         
                         painter.drawRect(QRectF(draw_x, draw_y, 4, 4))
                         count += 1
                         
                     # Draw Viewport Box
                     view_poly = self.mapToScene(self.viewport().rect())
                     view_rect = view_poly.boundingRect()
                     
                     vx = (view_rect.x() - scene_rect.x()) * scale
                     vy = (view_rect.y() - scene_rect.y()) * scale
                     vw = view_rect.width() * scale
                     vh = view_rect.height() * scale
                     
                     draw_vx = map_rect.left() + vx + (map_size - scene_rect.width()*scale)/2
                     draw_vy = map_rect.top() + vy + (map_size - scene_rect.height()*scale)/2
                     
                     painter.setBrush(Qt.BrushStyle.NoBrush)
                     painter.setPen(QColor(255, 0, 0, 200))
                     painter.drawRect(QRectF(draw_vx, draw_vy, vw, vh))

        except Exception as e:
            logger.error(f"Minimap error: {e}")

        painter.restore()

    def on_selection_changed(self):
        items = self.scene.selectedItems()
        if not items:
            # Reset highlighting if nothing selected
            for item in self.scene.items():
                item.setOpacity(1.0)
            return

        if items and isinstance(items[0], NodeItem):
            node = items[0]
            file_path = node.params.get("file", "")
            lineno = node.params.get("lineno", 0)
            if file_path:
                self.node_selected.emit(file_path, lineno)
            
            # Highlight connected nodes (Data Flow Visualization)
            self.highlight_connected_nodes(node)

    def highlight_connected_nodes(self, root_node):
        """
        Optimized graph traversal for highlighting connected nodes (Upstream & Downstream).
        Uses BFS with adjacency lists (socket.edges) instead of scene iteration.
        """
        # 1. Dim all items first
        # Optimization: Only dim if not already dimmed to avoid unnecessary repaints?
        # But we need to reset anyway.
        # Batch operation?
        for item in self.scene.items():
             item.setOpacity(0.1) # Dim more for better contrast
        
        # 2. Traverse Graph
        visited_nodes = {root_node}
        visited_edges = set()
        queue = [root_node]
        
        while queue:
            current_node = queue.pop(0)
            
            # Downstream (Outputs -> Targets)
            for socket in current_node.output_sockets:
                # Use the socket's edge list (O(1) access)
                for edge in socket.edges:
                    if edge not in visited_edges:
                        visited_edges.add(edge)
                        # Ensure edge is valid
                        if edge.target_socket and edge.target_socket.parent_node:
                            target_node = edge.target_socket.parent_node
                            if target_node not in visited_nodes:
                                visited_nodes.add(target_node)
                                queue.append(target_node)
            
            # Upstream (Inputs <- Sources)
            for socket in current_node.input_sockets:
                for edge in socket.edges:
                    if edge not in visited_edges:
                        visited_edges.add(edge)
                        if edge.source_socket and edge.source_socket.parent_node:
                            source_node = edge.source_socket.parent_node
                            if source_node not in visited_nodes:
                                visited_nodes.add(source_node)
                                queue.append(source_node)

        # 3. Restore Opacity for Connected Subgraph
        for node in visited_nodes:
            node.setOpacity(1.0)
            # Ensure sockets are visible too if they are separate items (they are children usually)
            
        for edge in visited_edges:
            edge.setOpacity(1.0)

    def select_node_by_code_location(self, file_path, lineno):
        """Highlight node corresponding to code location"""
        target_node = None
        min_dist = float('inf')
        
        # Normalize file path
        search_path = file_path.replace("\\", "/").lower()
        
        for node in self.scene.nodes:
            node_file = node.params.get("file", "").replace("\\", "/").lower()
            node_line = node.params.get("lineno", 0)
            
            if search_path.endswith(node_file) or node_file.endswith(search_path):
                # Found file match, check line distance
                # We assume the function definition line is the start. 
                # If cursor is inside function (line > node_line), it's a match candidate.
                # We want the node with the largest line number that is <= cursor line.
                if lineno >= node_line:
                    dist = lineno - node_line
                    if dist < min_dist:
                        min_dist = dist
                        target_node = node
        
        self.scene.clearSelection()
        if target_node:
            target_node.setSelected(True)
            self.centerOn(target_node)
    
    def highlight_nodes_by_ids(self, node_ids):
        """Highlight nodes based on ID list from AI query"""
        if not node_ids: return
        
        self.scene.clearSelection()
        
        # Dim all first
        for item in self.scene.items():
            item.setOpacity(0.2)
            
        highlighted_count = 0
        for node in self.scene.nodes:
            # Check ID match (using ID or title as fallback if ID is ephemeral)
            # In build_graph, we assigned numeric IDs. 
            # If node_ids contains integers:
            try:
                # Find node with matching ID in params or temp_id if available?
                # The node_ids from AI query are based on the simplified summary passed to AI.
                # The summary used `id` field from graph_data.
                # We need to map back.
                # NodeItem doesn't store the original graph ID by default unless we put it in params.
                # But deserialization stores it in node_map. 
                # Let's check params for 'id' if we saved it? No we didn't save ID in params explicitly in builder.
                # However, serialize uses list index as ID.
                # In deserialize, we don't persist that ID on the NodeItem object itself except maybe implicitly.
                
                # Better approach: Match by Title which is unique in our graph builder usually
                # AI might return IDs, let's assume we can map.
                # Actually, in query_graph I sent: "id: title".
                # If AI returns IDs, I can map if I have the map.
                
                # Simplified: Match by title if ID matching is hard
                pass
            except:
                pass
                
        # Alternative: The AI prompt I wrote returns "node_ids".
        # I should have used titles for robustness or ensured ID persistence.
        # Let's update `query_graph` to return Titles or use fuzzy match on titles.
        
        # Assuming for now we just filter by text search logic as fallback or upgrade this later.
        pass

    def highlight_nodes_by_titles(self, titles):
        """Highlight nodes based on title list from AI query"""
        if not titles: return
        
        self.scene.clearSelection()
        
        # Dim all first
        for item in self.scene.items():
            item.setOpacity(0.2)
            
        for node in self.scene.nodes:
            if node.title in titles:
                node.setOpacity(1.0)
                node.setSelected(True)
                
    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        current_scale = self.transform().m11()
        
        if current_scale < 0.05 and event.angleDelta().y() < 0: return
        if current_scale > 5.0 and event.angleDelta().y() > 0: return

        zoom_factor = zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        if isinstance(item, NodeSocket):
            self.start_socket = item
            self.temp_edge = NodeEdge(item, None, self.mapToScene(event.pos()))
            self.scene.addItem(self.temp_edge)
            return
        
        if event.button() == Qt.MouseButton.RightButton:
            if isinstance(item, NodeItem) or (item and isinstance(item.parentItem(), NodeItem)):
                node = item if isinstance(item, NodeItem) else item.parentItem()
                from PyQt6.QtWidgets import QMenu
                menu = QMenu(self)
                act_edit = menu.addAction("Edit Params")
                if node.node_type == "Module":
                    if node.params.get("module") in self.scene.collapsed_modules:
                        act_toggle = menu.addAction("Expand Module")
                    else:
                        act_toggle = menu.addAction("Collapse Module")
                chosen = menu.exec(self.mapToGlobal(event.pos()))
                if chosen == act_edit:
                    self.edit_node_params(node)
                elif 'act_toggle' in locals() and chosen == act_toggle:
                    if node.params.get("module") in self.scene.collapsed_modules:
                        self.scene.expand_module_for_node(node)
                    else:
                        self.scene.collapse_module_for_node(node)
                return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.start_socket and self.temp_edge:
            self.temp_edge.target_point = self.mapToScene(event.pos())
            self.temp_edge.update_path()
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            for item in self.scene.selectedItems():
                if isinstance(item, NodeEdge):
                    self.scene.remove_edge(item)
                elif isinstance(item, NodeItem):
                    # Remove edges first
                    for socket in item.input_sockets + item.output_sockets:
                         for edge in list(socket.edges):
                             self.scene.remove_edge(edge)
                    self.scene.removeItem(item)
                    if item in self.scene.nodes:
                        self.scene.nodes.remove(item)
            self.save_state()
        else:
            super().keyPressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.start_socket:
            if self.temp_edge:
                self.scene.removeItem(self.temp_edge)
                self.temp_edge = None

            item = self.itemAt(event.pos())
            if isinstance(item, NodeSocket) and item != self.start_socket:
                if self.start_socket.is_output != item.is_output:
                    source = self.start_socket if self.start_socket.is_output else item
                    target = item if item.is_output == False else self.start_socket
                    self.scene.add_edge(source, target)
                    self.save_state()
            
            self.start_socket = None
            
        super().mouseReleaseEvent(event)
        if self.scene.selectedItems():
            self.save_state()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText(): event.accept()
        else: event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            node_type = event.mimeData().text()
            pos = self.mapToScene(event.position().toPoint())
            self.create_node_by_type(node_type, pos)
            event.accept()

    def create_node_by_type(self, node_type, pos):
        inputs = []
        outputs = []
        if node_type == "Read Image": outputs = ["image"]
        elif node_type == "Show Image": inputs = ["image"]
        elif node_type in ["Convert Color", "Gaussian Blur", "Canny Edge"]:
            inputs = ["image"]; outputs = ["image"]
        
        node = NodeItem(node_type, inputs, outputs)
        node.setPos(pos)
        params = {}
        if node_type == "Read Image": params["file_path"] = "image.jpg"
        elif node_type == "Gaussian Blur": params["ksize"] = 5
        elif node_type == "Canny Edge": params["threshold1"] = 100; params["threshold2"] = 200
        
        node.set_params(params)
        self.scene.add_node(node)
        self.save_state()

    def edit_node_params(self, node):
        if not hasattr(node, "params"): node.params = {}
        text_data = json.dumps(node.params, indent=2)
        text, ok = QInputDialog.getMultiLineText(self, f"Edit {node.title} Params", "JSON Params:", text_data)
        if ok:
            try:
                new_params = json.loads(text)
                node.set_params(new_params)
                self.save_state()
            except Exception as e:
                logger.error(f"Invalid JSON: {e}")

    def save_state(self):
        try:
            data = self.scene.serialize()
            with open("autosave.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("Graph autosaved")
        except Exception as e:
            logger.error(f"Autosave failed: {e}")

    def load_state(self):
        if os.path.exists("autosave.json"):
            try:
                with open("autosave.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.scene.deserialize(data)
                logger.info("Graph loaded from autosave")
            except Exception as e:
                logger.error(f"Load failed: {e}")

    def center_view(self):
        if self.scene.items():
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.scale(0.9, 0.9)

    def filter_nodes(self, text):
        if not text:
            for item in self.scene.items():
                if isinstance(item, NodeItem):
                    item.setOpacity(1.0)
            return

        text = text.lower()
        for item in self.scene.items():
            if isinstance(item, NodeItem):
                match = False
                if text in item.title.lower(): match = True
                if hasattr(item, 'params'):
                    file_name = item.params.get("file", "").lower()
                    if text in file_name: match = True
                item.setOpacity(1.0 if match else 0.2)
