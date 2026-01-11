import networkx as nx
import math
import os
import json
from utils.logger import logger

class CodeGraphBuilder:
    def __init__(self):
        self.NODE_WIDTH = 250
        self.NODE_HEIGHT = 100
        # Increased spacing for better separation
        self.LAYER_SPACING_X = 400  # Horizontal spacing (Logic Layers)
        self.LAYER_SPACING_Y = 300  # Vertical spacing (Physical Layers)
        self.NODE_SPACING_Y = 120   # Vertical spacing between nodes in same layer
        # Safety thresholds for huge graphs
        self.MAX_NODES = 600
        self.MAX_EDGES = 1000
        self.EDGE_CYCLE_CHECK_LIMIT = 200
        
        try:
            from core.options_manager import options_manager
            self.MIN_SPACING = int(options_manager.settings.get("min_spacing", 30))
            # Cap user settings to prevent crashes
            user_node_limit = int(options_manager.settings.get("graph_node_limit", self.MAX_NODES))
            self.graph_node_limit = min(user_node_limit, 2000)
            self.graph_edge_limit = int(options_manager.settings.get("graph_edge_limit", self.MAX_EDGES))
        except Exception:
            self.MIN_SPACING = 30
            self.graph_node_limit = self.MAX_NODES
            self.graph_edge_limit = self.MAX_EDGES

        # Layer Definitions
        self.PHYSICAL_LAYERS = {
            "INPUT_SOURCE": 0,
            "PROCESSING": 1,
            "COMPUTATION": 2,
            "OUTPUT": 3,
            "OTHER": 4
        }
        
        self.LOGIC_LAYERS = {
            "ROOT": 0,
            "MODULE": 1,
            "FILE": 2,
            "LOGIC": 3
        }

        # Visual Styles (Colors from proposal)
        self.STYLES = {
            "INPUT_SOURCE": {"color": "#E3F2FD", "border": "#2196F3"},      # Light Blue
            "PROCESSING": {"color": "#E0F7FA", "border": "#00BCD4"}, # Cyan
            "COMPUTATION": {"color": "#E8F5E9", "border": "#4CAF50"}, # Light Green
            "OUTPUT": {"color": "#F3E5F5", "border": "#9C27B0"}, # Light Purple
            "OTHER": {"color": "#F5F5F5", "border": "#9E9E9E"}# Light Gray
        }

    def _classify_node(self, node_id, attrs):
        """
        Classify node into Physical and Logical layers.
        Returns: (physical_layer_index, logical_layer_index, style_key)
        """
        # 0. Check manual override from relations.json (stored in attrs)
        if "layer" in attrs:
            manual_layer = attrs["layer"].upper()
            if manual_layer in self.PHYSICAL_LAYERS:
                return (self.PHYSICAL_LAYERS[manual_layer], self.LOGIC_LAYERS.get("MODULE", 1), manual_layer)

        file_path = attrs.get("file", "").lower()
        node_type = attrs.get("type", "Function")
        
        # --- Physical Layer Classification ---
        physical = "OTHER" # Default
        
        # 1. Input Source
        if node_type in ["Read Image", "Video Capture", "Input"]:
            physical = "INPUT_SOURCE"
            
        # 2. Processing (OpenCV)
        elif node_type in ["Canny Edge", "Convert Color", "Gaussian Blur"] or "cv2." in node_id:
            physical = "PROCESSING"
            
        # 3. Computation (Generic Function)
        elif node_type == "GenericFunction" or node_type == "Function":
            physical = "COMPUTATION"
            
        # 4. Output
        elif node_type in ["Show Image", "Save Image", "Output"]:
            physical = "OUTPUT"
            
        # --- Logical Layer Classification ---
        # Default Logic Layer based on type
        logical = "LOGIC"
        
        if node_type == "Project" or node_id == "root":
            logical = "ROOT"
        elif node_type == "Module":
            logical = "MODULE"
        elif node_type == "File":
            logical = "FILE"
            
        return (self.PHYSICAL_LAYERS[physical], self.LOGIC_LAYERS[logical], physical)

    def build_graph(self, analysis_result, trace_data=None):
        """
        Convert analysis result to node graph data format with strict layered layout.
        Optional trace_data (list of dicts) to highlight hit counts.
        """
        logger.info("Starting graph layout generation...")
        if not analysis_result:
            return None

        # Safety: If graph is huge, switch to file-level aggregation mode
        total_funcs = len(analysis_result.get("functions", []))
        total_calls = len(analysis_result.get("calls", []))
        if total_funcs > self.graph_node_limit or total_calls > self.graph_edge_limit:
            logger.info(f"Graph exceeds safety thresholds (funcs={total_funcs}, calls={total_calls}). Using aggregated file-level graph.")
            return self._build_aggregated_file_graph(analysis_result)

        # Process Trace Data if available
        hit_counts = {}
        if trace_data:
            for t in trace_data:
                # Map trace source/target to graph nodes
                tgt = t.get("target")
                if tgt:
                    hit_counts[tgt] = hit_counts.get(tgt, 0) + 1
                    
        G = nx.DiGraph()
        
        # 0. Merge relations.json
        rel_path = os.path.join(os.getcwd(), "relations.json")
        relations = []
        if os.path.exists(rel_path):
            try:
                with open(rel_path, "r", encoding="utf-8") as f:
                    relations = json.load(f)
            except Exception:
                relations = []
        
        # 1. Add Nodes
        for func in analysis_result.get("functions", []):
            node_id = func["name"]
            # Infer minimal attributes if missing
            if "file" not in func:
                func["file"] = "unknown"
                
            G.add_node(node_id, **func)
            
        # 2. Add Edges
        for call in analysis_result.get("calls", []):
            if G.has_node(call["source"]) and G.has_node(call["target"]):
                G.add_edge(call["source"], call["target"], **call)
        
        # 2.1 Add relations.json edges
        for rel in relations:
            src = rel.get("source")
            tgt = rel.get("target")
            typ = rel.get("type", "default")
            
            weight = rel.get("weight", 1)
            risk = rel.get("risk_level", "low")
            layer = rel.get("layer", None) # Manual layer for node
            direction = rel.get("direction", "forward") # forward, bidirectional
            
            if src and not G.has_node(src):
                node_attrs = {"type": rel.get("node_type", "Module"), "file": "", "module": rel.get("module", "")}
                if layer: node_attrs["layer"] = layer
                G.add_node(src, **node_attrs)
                
            if tgt and not G.has_node(tgt):
                node_attrs = {"type": rel.get("node_type", "Module"), "file": "", "module": rel.get("module", "")}
                if layer: node_attrs["layer"] = layer
                G.add_node(tgt, **node_attrs)
                
            if src and tgt:
                G.add_edge(src, tgt, type=typ, weight=weight, risk=risk, direction=direction)
                if direction == "bidirectional":
                    G.add_edge(tgt, src, type=typ, weight=weight, risk=risk, direction=direction)
                
        # 3. Enhance Graph (Modules, Files if missing)
        # Ensure file nodes exist for all logic nodes
        files = set()
        for n, attrs in G.nodes(data=True):
            if attrs.get("file"):
                files.add(attrs["file"])
        
        for f in files:
            if not G.has_node(f):
                G.add_node(f, type="File", file=f, module="file_root", name=os.path.basename(f))
                
        # Link Logic to File
        for n, attrs in list(G.nodes(data=True)):
            if attrs.get("type") not in ["File", "Module"] and attrs.get("file"):
                if G.has_node(attrs["file"]):
                    # Inherit status from node for containment edge
                    edge_status = "unchanged"
                    if attrs.get("_status") == "added":
                        edge_status = "added"
                    elif attrs.get("_status") == "removed":
                        edge_status = "removed"
                        
                    G.add_edge(attrs["file"], n, type="contains", _status=edge_status)

        # --- Topological Sort for Execution Order ---
        execution_map = {}
        try:
            # Create a subgraph without cycles for sorting
            dag = G.copy()
            
            # Robust Cycle Breaking (Iterative)
            # Instead of simple_cycles (expensive), use iterative find_cycle
            while True:
                try:
                    cycle = nx.find_cycle(dag, orientation='original')
                    # cycle is list of edges (u, v, key...)
                    # Break the cycle by removing the last edge (back edge candidate)
                    u, v = cycle[-1][:2]
                    if dag.has_edge(u, v):
                        dag.remove_edge(u, v)
                except nx.NetworkXNoCycle:
                    break
                except Exception as e:
                    logger.warning(f"Cycle breaking error: {e}")
                    break
                
            topo_order = list(nx.topological_sort(dag))
            for i, node_id in enumerate(topo_order):
                execution_map[node_id] = i + 1
        except Exception as e:
            logger.warning(f"Topological sort failed: {e}")
            # Fallback: Sort by Name or In-Degree as proxy
            nodes_sorted = sorted(G.nodes(), key=lambda n: G.in_degree(n))
            for i, node_id in enumerate(nodes_sorted):
                execution_map[node_id] = i + 1

        # 4. Compute Layout
        pos = self._compute_layered_layout(G, execution_map)
        
        # 5. Serialize
        graph_data = {"nodes": [], "edges": []}
        node_id_map = {}
        
        # Find bounds for normalization
        if pos:
            min_x = min(p[0] for p in pos.values())
            min_y = min(p[1] for p in pos.values())
        else:
            min_x, min_y = 0, 0

        index = 0
        for node_name in G.nodes():
            if node_name not in pos: continue
            
            p = pos[node_name]
            x, y = float(p[0] - min_x + 100), float(p[1] - min_y + 100)
            
            attrs = G.nodes[node_name]
            phy_idx, log_idx, style_key = self._classify_node(node_name, attrs)
            style = self.STYLES[style_key]
            
            # Pass through status from GitAnalyzer
            status = attrs.get("_status", "unchanged")
            
            # Dead Code Detection
            hits = hit_counts.get(node_name, 0)
            is_dead = False
            if trace_data is not None and hits == 0 and attrs.get("type") in ["Function", "Method"]:
                 is_dead = True
            
            exec_seq = execution_map.get(node_name, 0)
            
            node_data = {
                "id": index,
                "title": node_name,
                "x": x,
                "y": y,
                "type": attrs.get("type", "Function"),
                "style": style, # Pass style to frontend
                "layer_info": {"physical": style_key, "logical": log_idx},
                "inputs": ["in"],
                "outputs": ["out"],
                "params": {
                    "func_name": node_name,
                    "file": attrs.get("file", ""),
                    "lineno": attrs.get("lineno", 0),
                    "doc": attrs.get("doc", ""),
                    "_status": status,
                    "_hits": hits,
                    "_is_dead": is_dead,
                    "_exec_seq": exec_seq
                }
            }
            graph_data["nodes"].append(node_data)
            node_id_map[node_name] = index
            index += 1
            
        # Detect Cycles
        cycles = []
        # Safety: Skip expensive cycle enumeration for huge graphs
        if G.number_of_edges() <= self.EDGE_CYCLE_CHECK_LIMIT:
            try:
                cycles = list(nx.simple_cycles(G))
            except Exception:
                cycles = []
        else:
            logger.info(f"Skipping detailed cycle check (edges={G.number_of_edges()} > {self.EDGE_CYCLE_CHECK_LIMIT})")
            # Minimal check: just find ONE cycle if exists? No, visualization needs list of cycles.
            # We just return empty list to avoid crash.
            cycles = []
            
        cycle_edges = set()
        for cycle in cycles:
            # Add all edges in the cycle to the set
            for i in range(len(cycle)):
                u, v = cycle[i], cycle[(i + 1) % len(cycle)]
                cycle_edges.add((u, v))
        
        for u, v, data in G.edges(data=True):
            if u in node_id_map and v in node_id_map:
                # Classify Edge
                u_phy = self._classify_node(u, G.nodes[u])[2] # Get key string
                v_phy = self._classify_node(v, G.nodes[v])[2]
                
                edge_type = "default"
                is_cycle = (u, v) in cycle_edges
                risk_level = data.get("risk", "low")
                
                if is_cycle:
                    edge_type = "cycle"
                    risk_level = "high" # Force high risk for cycles
                elif u_phy == "INPUT_SOURCE" and v_phy == "PROCESSING":
                    edge_type = "data_flow"
                elif u_phy == "PROCESSING" and v_phy == "COMPUTATION":
                    edge_type = "data_flow"
                elif u_phy == "COMPUTATION" and v_phy == "OUTPUT":
                    edge_type = "data_flow"
                elif data.get("type") == "module_flow":
                    edge_type = "module_flow"
                elif data.get("type") == "contains":
                    edge_type = "contains"
                
                status = data.get("_status", "unchanged")

                edge_data = {
                    "source": node_id_map[u],
                    "source_socket": 0,
                    "target": node_id_map[v],
                    "target_socket": 0,
                    "type": edge_type,
                    "weight": data.get("weight", 1),
                    "risk": risk_level,
                    "_status": status # Added field
                }
                graph_data["edges"].append(edge_data)
                
        return graph_data

    def _compute_layered_layout(self, G, execution_map={}):
        """
        Compute (x, y) for each node using Topological Generations.
        This ensures a clear Left-to-Right flowchart where dependencies always flow forward.
        """
        pos = {}
        
        # 1. Calculate Generations (Columns)
        generations = []
        try:
            # Create a cycle-free DAG for layout calculation
            dag = G.copy()
            
            # Fast greedy cycle breaking
            try:
                # Use simple heuristic: remove back edges based on existing execution_map if available
                if execution_map:
                    for u, v in list(dag.edges()):
                        if execution_map.get(u, 0) >= execution_map.get(v, 0):
                            dag.remove_edge(u, v)
                            
                # Fallback: iterative cycle breaking if still cyclic
                while True:
                    try:
                        cycle = nx.find_cycle(dag)
                        dag.remove_edge(cycle[-1][0], cycle[-1][1])
                    except nx.NetworkXNoCycle:
                        break
            except Exception:
                pass # Proceed with best effort

            # Compute Generations
            # topological_generations returns [[root_nodes], [depth_1], [depth_2]...]
            generations = list(nx.topological_generations(dag))
            
        except Exception as e:
            logger.warning(f"Layout generation failed: {e}. Using fallback bucket layout.")
            # Fallback: Bucket by execution sequence
            buckets = {}
            for n in G.nodes():
                seq = execution_map.get(n, 0)
                col = seq // 10 # 10 nodes per column roughly
                buckets.setdefault(col, []).append(n)
            generations = [buckets[k] for k in sorted(buckets.keys())]

        # 2. Assign Coordinates
        COLUMN_WIDTH = 450
        ROW_HEIGHT = 150
        
        # Track vertical usage per column to center them
        max_col_height = max(len(gen) for gen in generations) * ROW_HEIGHT if generations else 0
        
        for col_idx, nodes in enumerate(generations):
            # Sort nodes in column to minimize edge crossing?
            # Heuristic: sort by input-neighbor average Y?
            # For now, sort by name or type
            nodes.sort(key=lambda n: str(n))
            
            # Vertical Centering
            col_height = len(nodes) * ROW_HEIGHT
            start_y = (max_col_height - col_height) / 2
            
            base_x = col_idx * COLUMN_WIDTH
            
            for row_idx, node in enumerate(nodes):
                x = base_x
                y = start_y + row_idx * ROW_HEIGHT
                
                # Slight stagger for density
                if row_idx % 2 == 1:
                    x += 40
                    
                pos[node] = [x, y]
                
        return pos

    def _build_aggregated_file_graph(self, analysis_result):
        """
        Build a file-level aggregated graph to guarantee stability on huge projects.
        - Nodes: Files
        - Edges: Calls between files (weighted)
        """
        logger.info("Building aggregated file-level graph...")
        # Map function -> file
        func_to_file = {}
        file_func_count = {}
        for f in analysis_result.get("functions", []):
            fname = f.get("name")
            fpath = f.get("file", "unknown")
            func_to_file[fname] = fpath
            file_func_count[fpath] = file_func_count.get(fpath, 0) + 1

        # Build file edges with weights
        file_edges = {}
        for c in analysis_result.get("calls", []):
            s = func_to_file.get(c.get("source"))
            t = func_to_file.get(c.get("target"))
            if not s or not t:
                continue
            if s == t:
                continue
            key = (s, t)
            file_edges[key] = file_edges.get(key, 0) + 1

        # Build a graph of files
        Gf = nx.DiGraph()
        for fp, cnt in file_func_count.items():
            Gf.add_node(fp, type="File", file=fp, func_count=cnt)
        for (s, t), w in file_edges.items():
            Gf.add_edge(s, t, weight=w, type="file_flow")

        # Topological order fallback safe
        exec_map = {}
        try:
            dag = Gf.copy()
            # break cycles greedily
            while True:
                try:
                    cyc = nx.find_cycle(dag, orientation='original')
                    u, v = cyc[-1][:2]
                    if dag.has_edge(u, v):
                        dag.remove_edge(u, v)
                except nx.NetworkXNoCycle:
                    break
                except Exception:
                    break
            order = list(nx.topological_sort(dag))
            for i, nid in enumerate(order):
                exec_map[nid] = i + 1
        except Exception:
            # fallback: sort by indegree
            for i, nid in enumerate(sorted(Gf.nodes(), key=lambda n: Gf.in_degree(n))):
                exec_map[nid] = i + 1

        # Use standardized layout
        pos = self._compute_layered_layout(Gf, exec_map)

        # Serialize
        graph_data = {"nodes": [], "edges": [], "meta": {"mode": "aggregated_file", "file_count": len(Gf.nodes()), "edge_count": len(Gf.edges())}}
        node_id_map = {}
        idx = 0
        for n in Gf.nodes():
            p = pos.get(n, [0, 0])
            node_data = {
                "id": idx,
                "title": os.path.basename(n) if n else "unknown",
                "x": float(p[0] + 100),
                "y": float(p[1] + 100),
                "type": "File",
                "style": self.STYLES["OTHER"],
                "layer_info": {"physical": "OTHER", "logical": self.LOGIC_LAYERS["FILE"]},
                "inputs": ["in"],
                "outputs": ["out"],
                "params": {
                    "file": n,
                    "func_count": int(Gf.nodes[n].get("func_count", 0)),
                    "_exec_seq": int(exec_map.get(n, 0))
                }
            }
            graph_data["nodes"].append(node_data)
            node_id_map[n] = idx
            idx += 1
        for u, v, data in Gf.edges(data=True):
            if u in node_id_map and v in node_id_map:
                edge_data = {
                    "source": node_id_map[u],
                    "source_socket": 0,
                    "target": node_id_map[v],
                    "target_socket": 0,
                    "type": "file_flow",
                    "weight": int(data.get("weight", 1)),
                    "risk": "low",
                    "_status": "unchanged"
                }
                graph_data["edges"].append(edge_data)
        logger.info(f"Aggregated graph built: files={len(Gf.nodes())}, edges={len(Gf.edges())}")
        return graph_data

code_graph_builder = CodeGraphBuilder()
