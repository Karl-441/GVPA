import networkx as nx
from ai.plugin_manager import AIPlugin, AIPluginRegistry

class AIRiskGovernor(AIPlugin):
    def __init__(self):
        super().__init__()
        self.name = "AI Risk Governor"
        self.description = "Analyzes graph for architectural risks, cycles, and complexity."
        self.version = "1.0"

    def execute(self, context):
        """
        Context expects:
        - 'nodes': list of node dicts
        - 'edges': list of edge dicts
        """
        nodes = context.get("nodes", [])
        edges = context.get("edges", [])
        
        G = nx.DiGraph()
        for n in nodes:
            G.add_node(n["id"], title=n.get("title", "Unknown"))
        for e in edges:
            G.add_edge(e["source"], e["target"])
            
        risks = []
        suggestions = []
        
        # 1. Cycle Detection
        try:
            cycles = list(nx.simple_cycles(G))
            if cycles:
                for c in cycles:
                    names = [G.nodes[nid].get("title", nid) for nid in c]
                    risks.append({
                        "level": "Critical",
                        "type": "Circular Dependency",
                        "description": f"Cycle detected: {' -> '.join(names)}",
                        "nodes": c
                    })
                    suggestions.append(f"Break the cycle between {names[0]} and {names[-1]} by introducing an interface or event.")
        except Exception:
            pass # simple_cycles can be expensive on massive graphs
            
        # 2. God Object Detection (High Degree)
        degrees = dict(G.degree())
        if degrees:
            avg_degree = sum(degrees.values()) / len(degrees)
            threshold = max(10, avg_degree * 3)
            
            for nid, deg in degrees.items():
                if deg > threshold:
                    name = G.nodes[nid].get("title", nid)
                    risks.append({
                        "level": "Warning",
                        "type": "High Complexity",
                        "description": f"Node '{name}' has {deg} connections (High Coupling).",
                        "nodes": [nid]
                    })
                    suggestions.append(f"Refactor '{name}' by splitting responsibilities.")

        # 3. Dead Code (Isolated Nodes)
        for nid in G.nodes():
            if G.degree(nid) == 0:
                name = G.nodes[nid].get("title", nid)
                risks.append({
                    "level": "Info",
                    "type": "Dead Code",
                    "description": f"Node '{name}' is isolated.",
                    "nodes": [nid]
                })

        return {
            "status": "success",
            "risks": risks,
            "suggestions": suggestions,
            "message": f"Identified {len(risks)} risks."
        }

# Register on import
AIPluginRegistry.register(AIRiskGovernor)
