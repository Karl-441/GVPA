import re
from .base_parser import BaseParser

class DockerfileParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        for m in re.finditer(r'^\s*FROM\s+([^\s]+)', content, re.M):
            imports.append(m.group(1))
        return {"imports": imports, "classes": [], "functions": [], "calls": []}

