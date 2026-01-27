import asyncio
import hashlib
import json
import networkx as nx
from typing import Dict, Any, List, Optional
from utils.logger import logger
from engine.base import NodeRegistry, BaseNode
from engine.cache import NodeCache

class ExecutionEngine:
    def __init__(self):
        self.cache = NodeCache(max_size=50)

    def _compute_input_hash(self, node_id: str, node_type: str, inputs: Dict[str, Any], params: Dict[str, Any]) -> str:
        """
        Compute a hash for the node inputs to use as a cache key.
        """
        # Create a stable representation of inputs
        # For complex objects (like images), we might need a better way (e.g. object ID or content hash)
        # For now, we assume if it's a primitive, we hash it. If it's an object, we use its id().
        # Ideally, data passed between nodes should be immutable or versioned.
        
        hasher = hashlib.md5()
        hasher.update(node_type.encode())
        
        # Hash params
        try:
            param_str = json.dumps(params, sort_keys=True)
            hasher.update(param_str.encode())
        except:
            hasher.update(str(params).encode())
            
        # Hash inputs
        # Inputs are dicts of {name: data}
        sorted_keys = sorted(inputs.keys())
        for k in sorted_keys:
            v = inputs[k]
            # If input is a numpy array (image), hash its shape and some bytes? Too slow?
            # ComfyUI uses object IDs for outputs in memory.
            if hasattr(v, 'shape') and hasattr(v, 'dtype'): # Numpy/Torch
                # Using id for in-memory objects is safer for performance, assuming immutable workflow in one run
                # But across runs, we need content hashing if we want to persist cache?
                # For this session-based cache, id() or checking if it's the same object instance from previous run
                # Current simple cache is per-session.
                hasher.update(str(id(v)).encode())
            else:
                hasher.update(str(v).encode())
                
        return hasher.hexdigest()

    async def run_graph(self, graph_data: Dict[str, Any]) -> bool:
        """
        Execute the graph asynchronously.
        """
        logger.info("Starting Graph Execution...")
        
        # 1. Build Graph
        G = nx.DiGraph()
        node_map = {}
        
        for n_data in graph_data.get("nodes", []):
            nid = n_data["id"]
            node_map[nid] = n_data
            G.add_node(nid)
            
        connections = []
        for e_data in graph_data.get("edges", []):
            src = e_data["source"]
            tgt = e_data["target"]
            G.add_edge(src, tgt)
            connections.append(e_data)

        # 2. Check cycles
        if not nx.is_directed_acyclic_graph(G):
            logger.error("Graph contains cycles.")
            return False

        # 3. Topological Sort
        try:
            execution_order = list(nx.topological_sort(G))
        except Exception as e:
            logger.error(f"Topological sort failed: {e}")
            return False

        # 4. Execute
        runtime_nodes: Dict[str, BaseNode] = {}
        
        for nid in execution_order:
            n_data = node_map[nid]
            node_type = n_data["title"] # Assuming title is the type key
            params = n_data.get("params", {})
            
            # Prepare inputs from upstream
            # Current GVPA edge format: source, source_socket (index), target, target_socket (index)
            # New BaseNode expects named inputs.
            # We need a mapping strategy. 
            # Strategy: If node uses named inputs, we need to know which socket index maps to which name.
            # For now, let's assume BaseNode.INPUT_TYPES defines the order of keys -> indices.
            
            node_class = NodeRegistry.get_class(node_type)
            if not node_class:
                logger.error(f"Unknown node type: {node_type}")
                continue

            # Instantiate
            node_instance = node_class(node_id=nid, params=params)
            runtime_nodes[nid] = node_instance
            
            # Map inputs
            input_def = node_class.INPUT_TYPES()["required"]
            input_names = list(input_def.keys())
            
            node_inputs = {}
            
            # Find connections to this node
            my_connections = [c for c in connections if c["target"] == nid]
            
            for conn in my_connections:
                src_id = conn["source"]
                src_socket_idx = conn["source_socket"] # int
                tgt_socket_idx = conn["target_socket"] # int
                
                if src_id in runtime_nodes:
                    # Get output from source
                    # Source output is stored in node.outputs dict {index: data}
                    src_node = runtime_nodes[src_id]
                    input_data = src_node.get_output(src_socket_idx)
                    
                    # Set input on current node
                    # Map tgt_socket_idx to name if possible, or just pass to execute
                    if tgt_socket_idx < len(input_names):
                        input_name = input_names[tgt_socket_idx]
                        node_inputs[input_name] = input_data
                    else:
                        # Fallback for dynamic or index-based inputs
                        # node_instance.set_input(tgt_socket_idx, input_data)
                        pass
            
            # Check Cache
            cache_key = self._compute_input_hash(nid, node_type, node_inputs, params)
            cached_outputs = self.cache.get(cache_key)
            
            if cached_outputs:
                logger.info(f"Node {nid} ({node_type}): Cache Hit")
                node_instance.outputs = cached_outputs
            else:
                logger.info(f"Executing Node {nid}: {node_type}")
                try:
                    # Merge params into inputs for execution if they match input names
                    exec_kwargs = node_inputs.copy()
                    for p_name, p_val in params.items():
                        if p_name not in exec_kwargs:
                            exec_kwargs[p_name] = p_val

                    if asyncio.iscoroutinefunction(node_instance.execute):
                        results = await node_instance.execute(**exec_kwargs)
                    else:
                        results = node_instance.execute(**exec_kwargs)
                    
                    # Handle return values
                    # If tuple, map to indices
                    if isinstance(results, (tuple, list)):
                        for i, val in enumerate(results):
                            node_instance.outputs[i] = val
                    else:
                        node_instance.outputs[0] = results
                        
                    # Update Cache
                    self.cache.set(cache_key, node_instance.outputs)
                    
                except Exception as e:
                    logger.error(f"Error executing node {nid}: {e}")
                    import traceback
                    traceback.print_exc()
                    return False

        logger.info("Graph Execution Completed.")
        return True

execution_engine = ExecutionEngine()
