import ast
from .base_parser import BaseParser

class PythonParser(BaseParser):
    def parse(self, file_path, content):
        try:
            tree = ast.parse(content)
            visitor = StructureVisitor()
            visitor.visit(tree)
            return {
                "imports": visitor.imports,
                "classes": visitor.classes,
                "functions": visitor.functions,
                "calls": visitor.calls
            }
        except Exception as e:
            print(f"Error parsing Python file {file_path}: {e}")
            return None

class StructureVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = []
        self.classes = []
        self.functions = []
        self.calls = []
        self.current_scope = "global"

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        module = node.module or ''
        for alias in node.names:
            self.imports.append(f"{module}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        prev_scope = self.current_scope
        self.current_scope = node.name
        
        class_info = {
            "name": node.name,
            "bases": [self._get_base_name(base) for base in node.bases],
            "methods": [],
            "doc": ast.get_docstring(node) or "",
            "lineno": node.lineno
        }
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_info = {
                    "name": item.name,
                    "args": [arg.arg for arg in item.args.args],
                    "decorators": [self._get_decorator_name(d) for d in item.decorator_list],
                    "doc": ast.get_docstring(item) or "",
                    "lineno": item.lineno
                }
                class_info["methods"].append(method_info)
                self.current_scope = f"{node.name}.{item.name}"
                self.generic_visit(item)
                self.current_scope = node.name 
        
        self.classes.append(class_info)
        self.current_scope = prev_scope

    def visit_FunctionDef(self, node):
        if "." in self.current_scope: 
             self.generic_visit(node)
             return

        if self.current_scope != "global":
             self.generic_visit(node)
             return

        prev_scope = self.current_scope
        self.current_scope = node.name
        
        func_info = {
            "name": node.name,
            "args": [arg.arg for arg in node.args.args],
            "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
            "doc": ast.get_docstring(node) or "",
            "lineno": node.lineno
        }
        
        for d in node.decorator_list:
            dec_name = self._get_decorator_name(d)
            if any(x in dec_name for x in [".route", ".get", ".post", ".put", ".delete"]):
                func_info["type"] = "api_route"
                route_path = self._get_decorator_args(d)
                if route_path:
                    func_info["route"] = route_path
                    
        self.functions.append(func_info)
        self.generic_visit(node)
        self.current_scope = prev_scope

    def visit_Call(self, node):
        func_name = self._get_func_name(node.func)
        if func_name:
            call_info = {"source": self.current_scope, "target": func_name}
            
            if "requests." in func_name or "httpx." in func_name or "urllib." in func_name:
                call_info["type"] = "api_call"
                if node.args and isinstance(node.args[0], ast.Constant):
                     call_info["url"] = node.args[0].value
                elif node.keywords:
                     for k in node.keywords:
                         if k.arg == "url" and isinstance(k.value, ast.Constant):
                             call_info["url"] = k.value.value
            
            elif func_name.endswith(".emit") or "signal" in func_name.lower():
                call_info["type"] = "event_emit"
            
            self.calls.append(call_info)
        self.generic_visit(node)

    def _get_decorator_name(self, decorator):
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            return f"{self._get_func_name(decorator.value)}.{decorator.attr}"
        elif isinstance(decorator, ast.Call):
            return self._get_func_name(decorator.func)
        return "decorator"

    def _get_decorator_args(self, decorator):
        if isinstance(decorator, ast.Call) and decorator.args:
            if isinstance(decorator.args[0], ast.Constant):
                return decorator.args[0].value
        return None

    def _get_func_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_func_name(node.value)}.{node.attr}" if node.value else node.attr
        return None

    def _get_base_name(self, base):
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return f"{base.value.id}.{base.attr}" if isinstance(base.value, ast.Name) else "ComplexBase"
        return "Unknown"
