import re
from .base_parser import BaseParser

class YAMLParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        for m in re.finditer(r'url:\s*([^\s]+)', content):
            imports.append(m.group(1))
        return {"imports": imports, "classes": [], "functions": [], "calls": []}

