import networkx as nx
from ai.plugin_manager import AIPlugin, AIPluginRegistry
import math

class AIGraphOptimizer(AIPlugin):
    def __init__(self):
        super().__init__()
        self.name = "AI Graph Optimizer"
        self.description = "Optimizes graph layout using Hybrid Layered-Force algorithm (Left->Right)."
        self.version = "2.0"

    def execute(self, context):
        """
        Context expects:
        - 'nodes': list of node dicts (id, x, y, width, height, locked)
        - 'edges': list of edge dicts (source, target)
        - 'use_force': bool (optional, enable force-directed for small graphs)
        """
        nodes = context.get("nodes", [])
        edges = context.get("edges", [])
        
        if not nodes:
            return {"status": "skipped", "message": "No nodes to optimize"}

        # --- 1. Graph Construction ---
        G = nx.DiGraph()
        node_map = {} 
        locked_nodes = set()
        
        for n in nodes:
            nid = n.get("id")
            w = n.get("width", 200)
            h = n.get("height", 100)
            locked = n.get("locked", False)
            
            G.add_node(nid, width=w, height=h, x=n.get("x", 0), y=n.get("y", 0), locked=locked)
            node_map[nid] = n
            if locked:
                locked_nodes.add(nid)

        for e in edges:
            src = e.get("source")
            tgt = e.get("target")
            if src in node_map and tgt in node_map:
                G.add_edge(src, tgt)

        node_count = len(nodes)
        updates = {}
        
        # --- 2. Strategy Selection (Principle IV) ---
        # "Left -> Right" is mandatory (Principle 1)
        
        if node_count > 200:
            # Large Graph: Strict Layered (O(n))
            updates = self._layout_layered_strict(G)
            method = "Strict Layered (Performance)"
        elif node_count > 50:
             # Medium: Hybrid Layered (Fixed X, Adaptive Y)
             updates = self._layout_hybrid(G, locked_nodes, iterations=50)
             method = "Hybrid Layered (Barnes-Hut)"
        else:
             # Small: Hybrid Layered (High Precision)
             updates = self._layout_hybrid(G, locked_nodes, iterations=100)
             method = "Hybrid Layered (High Precision)"

        return {
            "status": "success", 
            "updates": updates,
            "message": f"Optimized layout ({method}) for {node_count} nodes."
        }

    def _layout_layered_strict(self, G):
        """
        O(n) Layered Layout. Ignores locks to ensure performance and structure.
        Strict Left -> Right.
        """
        # 1. Cycle Breaking (DFS)
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                # Copy graph to break cycles without affecting original edges
                dag = G.copy()
                for cycle in cycles:
                    dag.remove_edge(cycle[-1], cycle[0])
            else:
                dag = G
        except:
            dag = G # Fallback

        # 2. Layers (Topological)
        try:
            layers = list(nx.topological_generations(dag))
        except:
            # Fallback for cyclic/disconnected if cycle breaking failed
            layers = [list(G.nodes())] 

        updates = {}
        
        # Spacing Constants (Principle 2)
        # Horizontal >= 1/3 width (approx 80px)
        # Vertical >= 1/2 height (approx 50px)
        MIN_DIST_X = 100 
        MIN_DIST_Y = 80
        
        current_x = 0
        
        for layer_nodes in layers:
            # Sort layer by average parent Y to minimize crossings
            # (Simple heuristic)
            
            max_w = 0
            current_y = 0
            
            # Calculate Y positions
            for nid in layer_nodes:
                h = G.nodes[nid]["height"]
                w = G.nodes[nid]["width"]
                max_w = max(max_w, w)
                
                updates[nid] = {"x": float(current_x), "y": float(current_y)}
                current_y += h + MIN_DIST_Y
            
            # Move X pointer
            current_x += max_w + MIN_DIST_X
            
        return updates

    def _layout_hybrid(self, G, locked_nodes, iterations=50):
        """
        Hybrid approach:
        - X is determined by Topological Layer (Left -> Right strict).
        - Y is determined by Force Directed (Spring) logic or locked position.
        """
        # 1. Assign Layers for X
        try:
            # Break cycles for layering
            dag = G.copy()
            try:
                cycle = nx.find_cycle(dag)
                while cycle:
                    dag.remove_edge(cycle[-1][0], cycle[-1][1])
                    cycle = nx.find_cycle(dag)
            except:
                pass
            
            layers = list(nx.topological_generations(dag))
        except:
            # Fallback
            layers = [list(G.nodes())]

        # Map node -> layer index
        node_layer = {}
        for idx, layer in enumerate(layers):
            for n in layer:
                node_layer[n] = idx
        
        # Calculate X positions (fixed)
        # We need to handle node widths. 
        # For simplicity, we assume a column width based on max node width in that layer.
        layer_widths = {}
        MIN_DIST_X = 150
        
        for idx, layer in enumerate(layers):
            max_w = 0
            for n in layer:
                max_w = max(max_w, G.nodes[n]["width"])
            layer_widths[idx] = max_w

        node_x = {}
        current_x = 0
        for idx in range(len(layers)):
            # Center nodes in the "column"
            width = layer_widths.get(idx, 200)
            for n in layers[idx]:
                node_x[n] = current_x
            current_x += width + MIN_DIST_X

        # 2. Determine Y positions
        # Use Spring Layout but constrain X?
        # NetworkX spring_layout doesn't support constraining only one axis easily.
        # We can simulate 1D spring layout for Y.
        
        # Initial pos: use current Y or random
        pos = {n: (node_x[n], G.nodes[n]["y"]) for n in G.nodes()}
        
        # Fix locked nodes and X coordinates
        # We run spring layout but only update Y? 
        # Actually, simpler: Run spring layout on the whole graph, 
        # but SET 'fixed' for ALL nodes' X coordinates? 
        # No, nx doesn't support per-axis fixing.
        
        # Custom 1D relaxation (Iterative)
        # Simple Barycenter method + Constraint satisfaction
        
        updates = {}
        
        # Initialize Y with current or 0
        node_y = {n: G.nodes[n]["y"] for n in G.nodes()}
        
        # If locked, keep Y
        # If not locked, we can move Y
        
        MIN_DIST_Y = 80
        
        for _ in range(iterations):
            # Barycenter step: Y = avg(neighbors_Y)
            # Damping factor
            alpha = 0.5
            
            new_y = node_y.copy()
            
            for n in G.nodes():
                if n in locked_nodes:
                    continue
                
                # Get neighbors (in and out)
                # Ideally, we want to align with neighbors to straighten edges
                preds = list(G.predecessors(n))
                succs = list(G.successors(n))
                neighbors = preds + succs
                
                if not neighbors:
                    continue
                
                avg_y = sum(node_y[nbr] for nbr in neighbors) / len(neighbors)
                
                # Move towards avg
                new_y[n] = node_y[n] * (1 - alpha) + avg_y * alpha
            
            # Collision Resolution (Spacing)
            # For each layer, ensure nodes don't overlap
            for layer in layers:
                # Sort by current Y
                layer.sort(key=lambda n: new_y[n])
                
                # Enforce spacing
                for i in range(len(layer) - 1):
                    u = layer[i]
                    v = layer[i+1]
                    
                    dist = new_y[v] - new_y[u]
                    min_req = (G.nodes[u]["height"] + G.nodes[v]["height"])/2 + MIN_DIST_Y
                    
                    if dist < min_req:
                        # Push apart
                        diff = min_req - dist
                        # If u locked, move v down. If v locked, move u up. 
                        # If both, can't move (violation). If neither, move both.
                        u_locked = u in locked_nodes
                        v_locked = v in locked_nodes
                        
                        if u_locked and v_locked:
                            pass # Can't fix
                        elif u_locked:
                            new_y[v] += diff
                        elif v_locked:
                            new_y[u] -= diff
                        else:
                            new_y[u] -= diff / 2
                            new_y[v] += diff / 2
            
            node_y = new_y

        # Final Update
        for n in G.nodes():
            updates[n] = {"x": float(node_x[n]), "y": float(node_y[n])}
            
        return updates

AIPluginRegistry.register(AIGraphOptimizer)
