import os
import re
from utils.logger import logger

class ArchitectureGuard:
    def __init__(self):
        self.rules = [] # List of dicts: {"from": pattern, "to": pattern, "allow": bool, "message": str}
        self.load_default_rules()

    def load_default_rules(self):
        # Default: Controllers cannot call DAOs directly (should go through Service)
        self.rules = [
            {
                "from": r".*Controller.*",
                "to": r".*DAO.*|.*Repository.*",
                "allow": False,
                "message": "Controller should not access DAO/Repository directly. Use Service layer."
            },
            {
                "from": r".*Service.*",
                "to": r".*Controller.*",
                "allow": False,
                "message": "Service layer should not call Controller layer (Reverse Dependency)."
            }
        ]

    def add_rule(self, from_pattern, to_pattern, allow=True, message=""):
        self.rules.append({
            "from": from_pattern,
            "to": to_pattern,
            "allow": allow,
            "message": message
        })

    def check_graph(self, graph_data):
        """
        Check the graph data against architecture rules.
        Returns a list of violations.
        """
        violations = []
        
        nodes = {n["id"]: n for n in graph_data.get("nodes", [])}
        
        for edge in graph_data.get("edges", []):
            source_node = nodes.get(edge["source"])
            target_node = nodes.get(edge["target"])
            
            if not source_node or not target_node:
                continue
                
            source_name = source_node["title"]
            target_name = target_node["title"]
            
            for rule in self.rules:
                match_src = re.match(rule["from"], source_name)
                match_dst = re.match(rule["to"], target_name)
                
                if match_src and match_dst:
                    if not rule["allow"]:
                        violations.append({
                            "source": source_name,
                            "target": target_name,
                            "message": rule["message"]
                        })
                        
        return violations

architecture_guard = ArchitectureGuard()
