import re
from .base_parser import BaseParser

class XMLParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        for m in re.finditer(r'href="([^"]+)"', content):
            imports.append(m.group(1))
        for m in re.finditer(r'src="([^"]+)"', content):
            imports.append(m.group(1))
        return {"imports": imports, "classes": [], "functions": [], "calls": []}

