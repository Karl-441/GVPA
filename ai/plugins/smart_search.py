from ai.plugin_manager import AIPlugin, AIPluginRegistry
from ai.llm_bridge import llm_client
from utils.logger import logger
import re

class SmartSearchAction(AIPlugin):
    def __init__(self):
        super().__init__()
        self.name = "Smart Search Assistant"
        self.description = "Intelligent search and navigation for massive node graphs."
        self.version = "1.0"

    def execute(self, context):
        """
        Context:
        - 'nodes': list of node dicts (full data)
        - 'query': str (search query)
        - 'use_llm': bool
        """
        nodes = context.get("nodes", [])
        query = context.get("query", "").strip()
        use_llm = context.get("use_llm", False)
        
        if not nodes or not query:
            return {"status": "skipped", "message": "No nodes or empty query"}

        matched_ids = []
        
        # 1. LLM-based Semantic Search (Optional)
        if use_llm and llm_client.is_available():
            # Ask LLM to extract keywords or intent
            # e.g. "Find all OpenCV nodes" -> type: "cv2", "opencv"
            intent = llm_client.chat_completion([
                {"role": "system", "content": "Extract search keywords and intent from user query. Return JSON with 'keywords' (list) and 'type_filter' (string or null)."},
                {"role": "user", "content": query}
            ])
            # For this implementation, we'll assume we parse the LLM output or fallback
            # But to keep it simple and robust for now, we'll just log and proceed to heuristic
            logger.info(f"LLM Search Intent: {intent}")
            
        # 2. Heuristic / Keyword Search
        query_lower = query.lower()
        keywords = query_lower.split()
        
        for node in nodes:
            # Check ID, Label, Type
            node_id = str(node.get("id", ""))
            label = str(node.get("label", "")).lower()
            node_type = str(node.get("type", "")).lower()
            params = str(node.get("params", "")).lower()
            
            score = 0
            
            # Exact ID match
            if query_lower == node_id.lower():
                score += 100
            
            # Label contains query
            if query_lower in label:
                score += 50
                
            # Type contains query
            if query_lower in node_type:
                score += 40
                
            # Keywords match
            match_count = sum(1 for k in keywords if k in label or k in node_type or k in params)
            if match_count > 0:
                score += 10 * match_count
            
            if score > 0:
                matched_ids.append({"id": node.get("id"), "score": score})
        
        # Sort by score
        matched_ids.sort(key=lambda x: x["score"], reverse=True)
        final_ids = [m["id"] for m in matched_ids]

        return {
            "status": "success",
            "matched_ids": final_ids,
            "message": f"Found {len(final_ids)} nodes matching '{query}'"
        }

AIPluginRegistry.register(SmartSearchAction)
