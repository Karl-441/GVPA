import re
import os
import ast
from ai.plugin_manager import AIPlugin, AIPluginRegistry
from utils.logger import logger
from ai.llm_bridge import llm_client

class AICodeAnalyzer(AIPlugin):
    def __init__(self):
        super().__init__()
        self.name = "AI Code Analyzer"
        self.description = "Analyzes code for dynamic calls and hidden dependencies using AST and Pattern Recognition (Optional LLM)."
        self.version = "1.2"
        
        # Regex Patterns for non-AST languages or fallback
        self.patterns = {
            "python": [
                (r'getattr\s*\(\s*(\w+)\s*,\s*["\'](\w+)["\']', "dynamic_call_getattr"), 
                (r'importlib\.import_module\s*\(\s*["\'](.*?)["\']', "dynamic_import"),
                (r'eval\s*\(\s*["\'](.*?)["\']', "eval_exec"),
                (r'exec\s*\(\s*["\'](.*?)["\']', "eval_exec"),
                (r'__import__\s*\(\s*["\'](.*?)["\']', "dynamic_import_magic"),
            ],
            "java": [
                (r'Class\.forName\s*\(\s*["\'](.*?)["\']', "java_reflection_class"),
                (r'\.invoke\s*\(', "java_reflection_invoke"),
                (r'Proxy\.newProxyInstance', "java_dynamic_proxy"),
            ],
            "cpp": [
                (r'dlopen\s*\(\s*["\'](.*?)["\']', "cpp_dynamic_load"),
                (r'LoadLibrary\s*\(\s*["\'](.*?)["\']', "cpp_dynamic_load_win"),
            ]
        }

    def execute(self, context):
        """
        Context expects:
        - 'project_path': str
        - 'use_llm': bool (optional, default False)
        - 'files': list (optional)
        """
        project_path = context.get("project_path")
        use_llm = context.get("use_llm", False)
        
        if not project_path:
            return {"status": "error", "message": "No project path provided"}

        findings = []
        suggested_edges = []
        
        # Walk and analyze
        for root, _, files in os.walk(project_path):
            for file in files:
                full_path = os.path.join(root, file)
                ext = file.split('.')[-1].lower()
                
                try:
                    with open(full_path, "r", encoding="utf-8", errors='ignore') as f:
                        content = f.read()
                        
                    # 1. AST Analysis for Python
                    if ext == "py":
                        ast_findings = self._analyze_python_ast(content, full_path)
                        findings.extend(ast_findings)
                    
                    # 2. Regex Analysis (Fallback & Multi-language)
                    lang_key = "python" if ext == "py" else ("java" if ext == "java" else ("cpp" if ext in ["cpp", "c", "h"] else None))
                    
                    if lang_key:
                        for pattern, type_ in self.patterns.get(lang_key, []):
                            matches = re.finditer(pattern, content)
                            for m in matches:
                                target = m.group(1) if m.groups() else "unknown"
                                findings.append({
                                    "file": full_path,
                                    "line": content[:m.start()].count('\n') + 1,
                                    "type": type_,
                                    "match": m.group(0),
                                    "target": target,
                                    "confidence": "medium"
                                })
                                
                                # If we found a specific target (e.g. module name), suggest an edge
                                if target and target != "unknown":
                                    suggested_edges.append({
                                        "source_file": full_path,
                                        "target_hint": target,
                                        "type": "dynamic_dependency"
                                    })

                    # 3. Optional LLM Analysis for complex snippets (Simulated trigger)
                    # Only analyze if we found "eval" or suspicious reflection but couldn't resolve target
                    if use_llm and llm_client.is_available():
                        # Heuristic: if file contains "eval" but regex target is unknown
                        if "eval" in content and any(f['type'] == 'eval_exec' and f['target'] == 'unknown' for f in findings if f['file'] == full_path):
                            # In a real scenario, we'd extract the function containing eval
                            # For now, we log that LLM would be invoked
                            logger.info(f"LLM analysis candidate: {full_path}")
                            pass

                except Exception as e:
                    logger.warning(f"Failed to analyze {full_path}: {e}")

        return {
            "status": "success",
            "findings": findings,
            "suggested_edges": suggested_edges,
            "message": f"Analysis complete. Found {len(findings)} dynamic patterns."
        }

    def _analyze_python_ast(self, content, file_path):
        results = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                # Detect getattr(obj, "string_literal")
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id == 'getattr':
                        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                            results.append({
                                "file": file_path,
                                "line": node.lineno,
                                "type": "ast_dynamic_call",
                                "target": node.args[1].value,
                                "confidence": "high"
                            })
                    # Detect importlib.import_module("string_literal")
                    elif isinstance(node.func, ast.Attribute) and node.func.attr == 'import_module':
                         if len(node.args) >= 1 and isinstance(node.args[0], ast.Constant):
                            results.append({
                                "file": file_path,
                                "line": node.lineno,
                                "type": "ast_dynamic_import",
                                "target": node.args[0].value,
                                "confidence": "high"
                            })
        except Exception:
            pass
        return results

# Register on import
AIPluginRegistry.register(AICodeAnalyzer)
