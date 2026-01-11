import re
from .base_parser import BaseParser

class KotlinParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        for m in re.finditer(r'^\s*import\s+([A-Za-z0-9_.]+)', content, re.M):
            imports.append(m.group(1))
        classes = []
        for m in re.finditer(r'\bclass\s+([A-Za-z_]\w*)', content):
            classes.append({"name": m.group(1), "bases": [], "methods": [], "lineno": 0, "doc": ""})
        functions = []
        for m in re.finditer(r'^\s*fun\s+([A-Za-z_]\w*)\s*\(([^)]*)\)', content, re.M):
            args = [a.strip().split(':')[0] for a in m.group(2).split(',') if a.strip()]
            functions.append({"name": m.group(1), "args": args, "type": "Function"})
        return {"imports": imports, "classes": classes, "functions": functions, "calls": []}

