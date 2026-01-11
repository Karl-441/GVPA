import re
from .base_parser import BaseParser

class RustParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        for m in re.finditer(r'^\s*use\s+([A-Za-z0-9_:]+)', content, re.M):
            imports.append(m.group(1))
        functions = []
        for m in re.finditer(r'^\s*fn\s+([A-Za-z_]\w*)\s*\(([^)]*)\)', content, re.M):
            args = [a.strip().split(':')[0] for a in m.group(2).split(',') if a.strip()]
            functions.append({"name": m.group(1), "args": args, "type": "Function"})
        return {"imports": imports, "classes": [], "functions": functions, "calls": []}

