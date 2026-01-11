from engine.nodes.opencv_nodes import NodeRegistry
from utils.logger import logger
import networkx as nx

class ExecutionEngine:
    def __init__(self):
        pass

    def run_graph(self, graph_data):
        """
        Execute the graph based on serialized data
        graph_data: dict from NodeGraphScene.serialize()
        """
        # 1. Build Graph using NetworkX for topological sort
        G = nx.DiGraph()
        node_map = {} # id -> node_data
        
        # Add nodes
        for n_data in graph_data.get("nodes", []):
            nid = n_data["id"]
            node_map[nid] = n_data
            G.add_node(nid)
            
        # Add edges
        connections = [] # (source_id, source_socket, target_id, target_socket)
        for e_data in graph_data.get("edges", []):
            src = e_data["source"]
            tgt = e_data["target"]
            G.add_edge(src, tgt)
            connections.append(e_data)

        # 2. Check cycles
        if not nx.is_directed_acyclic_graph(G):
            logger.error("Graph contains cycles, cannot execute.")
            return False

        # 3. Topological Sort
        try:
            execution_order = list(nx.topological_sort(G))
        except Exception as e:
            logger.error(f"Topological sort failed: {e}")
            return False

        # 4. Instantiate and Execute
        runtime_nodes = {} # nid -> BaseNode instance
        
        for nid in execution_order:
            n_data = node_map[nid]
            node_type = n_data["title"] # Assuming title maps to type for now
            
            # Create instance
            node_instance = NodeRegistry.create(node_type, node_id=nid, params=n_data.get("params", {}))
            if not node_instance:
                logger.error(f"Unknown node type: {node_type}")
                continue
                
            runtime_nodes[nid] = node_instance
            
            # Feed inputs from upstream
            # Find edges pointing to this node
            my_inputs = [c for c in connections if c["target"] == nid]
            for conn in my_inputs:
                src_id = conn["source"]
                src_socket = conn["source_socket"]
                tgt_socket = conn["target_socket"]
                
                if src_id in runtime_nodes:
                    data = runtime_nodes[src_id].get_output(src_socket)
                    node_instance.set_input(tgt_socket, data)
            
            # Execute
            logger.info(f"Executing Node {nid}: {node_type}")
            node_instance.execute()

        return True

execution_engine = ExecutionEngine()
