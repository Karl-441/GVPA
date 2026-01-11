import json
from .base_parser import BaseParser

class JSONParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        try:
            data = json.loads(content)
            def walk(obj):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        walk(v)
                elif isinstance(obj, list):
                    for v in obj:
                        walk(v)
                elif isinstance(obj, str):
                    if obj.startswith("http"):
                        imports.append(obj)
            walk(data)
        except Exception:
            pass
        return {"imports": imports, "classes": [], "functions": [], "calls": []}

