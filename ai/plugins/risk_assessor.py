from ai.plugin_manager import AIPlugin, AIPluginRegistry
from utils.logger import logger
import networkx as nx

class RiskCheckAction(AIPlugin):
    def __init__(self):
        super().__init__()
        self.name = "Smart Risk Governance"
        self.description = "Identifies potential risks, performance bottlenecks, and structural issues."
        self.version = "1.0"

    def execute(self, context):
        """
        Context:
        - 'nodes': list of node dicts
        - 'edges': list of edge dicts
        """
        nodes = context.get("nodes", [])
        edges = context.get("edges", [])
        
        if not nodes:
            return {"status": "skipped", "message": "No graph data"}

        risks = []
        suggestions = []
        
        # Build Graph
        G = nx.DiGraph()
        node_map = {n['id']: n for n in nodes}
        for n in nodes:
            G.add_node(n['id'], type=n.get('type', 'Unknown'))
        for e in edges:
            if e['source'] in node_map and e['target'] in node_map:
                G.add_edge(e['source'], e['target'])

        # 1. Structural Analysis
        
        # Detect Cycles
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                risks.append({
                    "type": "Critical",
                    "title": "Circular Dependency Detected",
                    "description": f"Found {len(cycles)} cycles. Loops can cause infinite execution.",
                    "nodes": [c for cycle in cycles for c in cycle]
                })
        except:
            pass # simple_cycles can be expensive on large graphs

        # Detect Dead Nodes (Leaf nodes that are not explicit 'Output'/'Save'/'Show' types)
        for n in G.nodes():
            out_degree = G.out_degree(n)
            node_type = node_map[n].get('type', '').lower()
            is_sink_type = any(t in node_type for t in ['save', 'output', 'show', 'display', 'write'])
            
            if out_degree == 0 and not is_sink_type:
                risks.append({
                    "type": "Warning",
                    "title": "Potential Dead End",
                    "description": f"Node '{node_map[n].get('label', n)}' has no outputs and is not a sink node.",
                    "nodes": [n]
                })

        # Detect Isolated Nodes
        for n in G.nodes():
            if G.degree(n) == 0:
                risks.append({
                    "type": "Info",
                    "title": "Isolated Node",
                    "description": f"Node '{node_map[n].get('label', n)}' is not connected to anything.",
                    "nodes": [n]
                })

        # 2. Performance Analysis (Heuristic)
        # Check for long chains?
        try:
            dag_longest = nx.dag_longest_path_length(G)
            if dag_longest > 20:
                suggestions.append({
                    "title": "Long Execution Chain",
                    "description": f"Max chain length is {dag_longest}. Consider parallelizing branches if possible."
                })
        except:
            pass # Not a DAG

        return {
            "status": "success",
            "risks": risks,
            "suggestions": suggestions,
            "message": f"Identified {len(risks)} potential issues."
        }

AIPluginRegistry.register(RiskCheckAction)
