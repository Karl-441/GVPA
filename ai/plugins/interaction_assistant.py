import difflib
from ai.plugin_manager import AIPlugin, AIPluginRegistry

class AIInteractionAssistant(AIPlugin):
    def __init__(self):
        super().__init__()
        self.name = "AI Interaction Assistant"
        self.description = "Smart search and navigation assistant for large graphs."
        self.version = "1.0"

    def execute(self, context):
        """
        Context expects:
        - 'query': str (User's natural language or keyword query)
        - 'nodes': list of node dicts (id, title, type, params)
        - 'edges': list of edge dicts (source, target)
        """
        query = context.get("query", "").lower()
        nodes = context.get("nodes", [])
        edges = context.get("edges", [])
        
        if not query:
            return {"status": "skipped", "message": "Empty query"}

        matches = []
        related_ids = set()

        # 1. Fuzzy Match Nodes
        for node in nodes:
            # Check Title
            title = node.get("title", "").lower()
            # Check Type
            ntype = node.get("type", "").lower()
            # Check Params
            params = str(node.get("params", {})).lower()
            
            # Simple keyword matching first
            score = 0
            if query in title: score += 3
            if query in ntype: score += 2
            if query in params: score += 1
            
            # Fuzzy fallback if no direct match
            if score == 0:
                ratio = difflib.SequenceMatcher(None, query, title).ratio()
                if ratio > 0.6: score += 1
            
            if score > 0:
                matches.append(node["id"])
                related_ids.add(node["id"])

        # 2. Context Expansion (Find immediate neighbors of matches)
        # "Show me dependencies of X"
        expand = any(k in query for k in ["dependency", "depend", "related", "connect", "usage", "who uses"])
        
        if expand and matches:
            # Build Adjacency
            adj = {} # id -> [neighbors]
            for e in edges:
                src = e["source"]
                tgt = e["target"]
                adj.setdefault(src, []).append(tgt)
                adj.setdefault(tgt, []).append(src) # Undirected for "related"
            
            new_related = set()
            for mid in matches:
                if mid in adj:
                    new_related.update(adj[mid])
            related_ids.update(new_related)

        return {
            "status": "success",
            "matches": list(matches),
            "highlight_ids": list(related_ids),
            "message": f"Found {len(matches)} direct matches and {len(related_ids)} related nodes."
        }

# Register on import
AIPluginRegistry.register(AIInteractionAssistant)
