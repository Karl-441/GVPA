import os
import ast
import time
from utils.logger import logger
from core.code_analyzer import CodeAnalyzer

class ProjectCodeAnalyzer:
    def __init__(self):
        self.file_analyzer = CodeAnalyzer()
        self.symbol_table = {} # full_name -> {"type": "Function/Class", "file": path, "args": [], "meta": {}}
        self.calls = [] # list of {source: full_name, target: partial_name, file: path}
        self.ignore_dirs = {
            "venv", "env", ".env", ".venv", 
            "node_modules", 
            ".git", ".svn", ".hg", 
            "__pycache__", 
            "build", "dist", 
            "site-packages",
            "migrations",
            ".idea", ".vscode"
        }
        self.use_ai = False

    def enable_ai(self, enabled=True):
        self.use_ai = enabled

    def analyze_project(self, root_path):
        """
        Analyze all python files in the project directory
        Returns: {
            "functions": [...],
            "classes": [...],
            "calls": [...]
        }
        """
        self.symbol_table = {}
        self.calls = []
        
        # 1. Scan and Analyze Individual Files
        for root, dirs, files in os.walk(root_path):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignore_dirs]
            
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, root_path)
                    
                    # Double check if any part of path is ignored (for nested cases like lib/site-packages)
                    path_parts = rel_path.split(os.sep)
                    if any(p in self.ignore_dirs for p in path_parts):
                        continue
                        
                    module_name = rel_path.replace(os.sep, ".").replace(".py", "")
                    
                    self._analyze_file(full_path, module_name)
                    
        # 2. Resolve Calls (Linkage)
        resolved_calls = []
        # Count call frequencies for connection strength
        call_counts = {} # (source, target) -> count
        
        for call in self.calls:
            source = call["source"]
            target = call["target"]
            
            resolved_target = None
            
            # Simple resolution: check if target exists in symbol table
            # Try exact match
            if target in self.symbol_table:
                resolved_target = target
            else:
                # Try finding target in keys (suffix match)
                matches = [k for k in self.symbol_table.keys() if k.endswith(f".{target}") or k == target]
                if len(matches) >= 1:
                     # Pick first match
                     resolved_target = matches[0]
            
            if resolved_target:
                key = (source, resolved_target)
                call_counts[key] = call_counts.get(key, 0) + 1
            elif call.get("type") in ["mq_pub", "mq_sub", "api_call", "db_access"]:
                 # AI generated external/implicit calls might not map to internal symbols
                 # We treat target as a generic node
                 resolved_calls.append(call)

        for (source, target), count in call_counts.items():
            resolved_calls.append({
                "source": source, 
                "target": target,
                "weight": count # Connection strength
            })
                
        # 3. Format Result for Graph Builder
        result = {
            "functions": [],
            "classes": [], 
            "calls": resolved_calls
        }
        
        # Calculate Complexity (Degree)
        # We need a temporary graph or just counts
        node_degrees = {}
        for call in resolved_calls:
            s, t = call["source"], call["target"]
            node_degrees[s] = node_degrees.get(s, 0) + 1
            node_degrees[t] = node_degrees.get(t, 0) + 1
        
        for name, info in self.symbol_table.items():
            # Add complexity metric to meta
            meta = info.get("meta", {}).copy()
            meta["complexity"] = node_degrees.get(name, 0)
            
            # Pass through function type/route info
            node_type = info.get("type", "Function") # Default to Function
            if info.get("api_route"):
                node_type = "API_Route"
                meta["route"] = info["api_route"]

            if info["type"] == "Function" or info["type"] == "Method":
                # We normalize everything to functions list but with extended types
                result["functions"].append({
                    "name": name,
                    "args": info["args"],
                    "file": info["file"],
                    "meta": meta,
                    "type": node_type # Custom type field for graph builder
                })
                
        return result

    def _analyze_file(self, file_path, module_name):
        try:
            analysis = self.file_analyzer.analyze_file(file_path)
        except RecursionError:
            logger.error(f"RecursionError analyzing file: {file_path} - Skipping.")
            return
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return
            
        if not analysis:
            return

        # Get File Metadata
        try:
            stats = os.stat(file_path)
            meta = {
                "size": stats.st_size,
                "modified": time.strftime('%Y-%m-%d %H:%M', time.localtime(stats.st_mtime))
            }
        except:
            meta = {"size": 0, "modified": "Unknown"}

        # Register Global Functions
        for func in analysis.get("functions", []):
            full_name = f"{module_name}.{func['name']}"
            self.symbol_table[full_name] = {
                "type": "Function",
                "file": file_path,
                "args": func["args"],
                "meta": meta,
                # Store extended info
                "api_route": func.get("route"),
                "func_type": func.get("type")
            }
            
        # Register Classes and Methods
        for cls in analysis.get("classes", []):
            cls_full_name = f"{module_name}.{cls['name']}"
            # We don't graph class definition itself as a node usually, but its methods
            for method in cls["methods"]:
                method_full_name = f"{cls_full_name}.{method['name']}"
                self.symbol_table[method_full_name] = {
                    "type": "Method",
                    "file": file_path,
                    "args": method["args"],
                    "meta": meta,
                    "api_route": method.get("route"), # If method decorators are parsed
                    "func_type": method.get("type")
                }
                
        # Collect Calls
        for call in analysis.get("calls", []):
            # source in analysis is local name (e.g. "MyClass.method")
            # we need to prefix with module
            local_source = call["source"]
            target = call["target"]
            call_type = call.get("type", "call")
            call_url = call.get("url")
            
            if local_source == "global":
                source_full = f"{module_name}.<main>" # special entry?
            else:
                source_full = f"{module_name}.{local_source}"
                
            self.calls.append({
                "source": source_full,
                "target": target,
                "file": file_path,
                "type": call_type,
                "url": call_url
            })
            
        # AI Enhancement
        if self.use_ai:
            from core.ai_manager import ai_manager
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                ai_relations = ai_manager.analyze_implicit_dependencies(content, file_path)
                for rel in ai_relations:
                    # Map AI source to full name if possible, else use file-level node
                    source = rel.get("source")
                    if source == os.path.basename(file_path):
                        source_full = f"{module_name}.<implicit>"
                        # Create implicit node if needed
                        if source_full not in self.symbol_table:
                            self.symbol_table[source_full] = {
                                "type": "ImplicitContext",
                                "file": file_path,
                                "args": [],
                                "meta": meta
                            }
                    else:
                        source_full = f"{module_name}.{source}"

                    self.calls.append({
                        "source": source_full,
                        "target": rel.get("target"),
                        "file": file_path,
                        "type": rel.get("type", "implicit"),
                        "details": rel.get("details")
                    })
            except Exception as e:
                logger.error(f"AI enhancement error for {file_path}: {e}")

project_analyzer = ProjectCodeAnalyzer()
