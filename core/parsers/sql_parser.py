import re
from .base_parser import BaseParser

class SQLParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        for m in re.finditer(r'\bFROM\s+([A-Za-z0-9_.]+)', content, re.I):
            imports.append(m.group(1))
        return {"imports": imports, "classes": [], "functions": [], "calls": []}

