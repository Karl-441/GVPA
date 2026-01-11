import networkx as nx
from ai.plugin_manager import AIPlugin, AIPluginRegistry
import math

class AIGraphOptimizer(AIPlugin):
    def __init__(self):
        super().__init__()
        self.name = "AI Graph Optimizer"
        self.description = "Optimizes graph layout using Hierarchical (Sugiyama-like) or Force-Directed algorithms."
        self.version = "1.1"

    def execute(self, context):
        """
        Context expects:
        - 'nodes': list of node dicts (id, x, y, width, height)
        - 'edges': list of edge dicts (source, target)
        """
        nodes = context.get("nodes", [])
        edges = context.get("edges", [])
        
        if not nodes:
            return {"status": "skipped", "message": "No nodes to optimize"}

        # Build NetworkX Graph
        G = nx.DiGraph()
        node_map = {} # id -> data
        
        for n in nodes:
            nid = n.get("id")
            # Default sizes if missing
            w = n.get("width", 220)
            h = n.get("height", 100)
            G.add_node(nid, width=w, height=h)
            node_map[nid] = n

        for e in edges:
            src = e.get("source")
            tgt = e.get("target")
            if src in node_map and tgt in node_map:
                G.add_edge(src, tgt)

        updates = {}
        
        # Strategy Selection
        if nx.is_directed_acyclic_graph(G):
            updates = self._layout_hierarchical(G)
            method = "Hierarchical"
        else:
            updates = self._layout_force_directed(G)
            method = "Force-Directed"
            
        return {
            "status": "success", 
            "updates": updates,
            "message": f"Optimized layout ({method}) for {len(nodes)} nodes."
        }

    def _layout_hierarchical(self, G):
        """Layered layout for DAGs"""
        # 1. Assign Layers (Topological Generations)
        layers = list(nx.topological_generations(G))
        
        # 2. Assign Coordinates
        updates = {}
        
        # Config
        layer_dist_y = 150 # Vertical gap between layers
        node_dist_x = 250  # Horizontal gap between nodes
        
        start_y = 0
        
        for layer_idx, layer_nodes in enumerate(layers):
            # Sort nodes in layer to minimize crossings (Heuristic: by avg position of parents)
            # Simple heuristic: keep current order or sort by ID
            # Better: if layer > 0, sort by average x of predecessors
            if layer_idx > 0:
                def get_avg_pred_x(node):
                    preds = list(G.predecessors(node))
                    if not preds: return 0
                    total_x = sum(updates.get(p, {}).get("x", 0) for p in preds)
                    return total_x / len(preds)
                
                layer_nodes.sort(key=get_avg_pred_x)
            
            # Calculate total width of this layer
            layer_width = (len(layer_nodes) - 1) * node_dist_x
            start_x = -layer_width / 2 # Center the layer
            
            current_y = start_y + layer_idx * layer_dist_y
            
            for i, nid in enumerate(layer_nodes):
                current_x = start_x + i * node_dist_x
                updates[nid] = {"x": float(current_x), "y": float(current_y)}
                
        return updates

    def _layout_force_directed(self, G):
        """Force-directed layout for cyclic graphs"""
        # k is optimal distance. Larger = more spread.
        # Scale k by sqrt of node count to keep density reasonable
        k_val = 400 / (len(G.nodes) ** 0.5) if len(G.nodes) > 0 else 200
        
        pos = nx.spring_layout(G, k=k_val, iterations=100, seed=42, scale=1000)
        
        updates = {}
        for nid, (x, y) in pos.items():
            # Spring layout returns coords in [-1, 1] usually (unless scaled)
            # We used scale=1000, so [-1000, 1000]
            updates[nid] = {
                "x": float(x), 
                "y": float(y)
            }
        return updates

# Register on import
AIPluginRegistry.register(AIGraphOptimizer)
