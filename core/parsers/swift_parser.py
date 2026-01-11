import re
from .base_parser import BaseParser

class SwiftParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        # Swift: import Foundation
        for m in re.finditer(r'^\s*import\s+([\w\.]+)', content, re.M):
            imports.append(m.group(1))

        classes = []
        # Swift: class MyClass: BaseClass
        # Also structs and protocols
        type_pattern = r'(?:public|private|internal|fileprivate|open)?\s*(?:class|struct|protocol|extension)\s+([A-Za-z_]\w*)(?:\s*:\s*([A-Za-z_][\w\.,\s]*))?'
        for m in re.finditer(type_pattern, content):
            name = m.group(1)
            bases = [b.strip() for b in m.group(2).split(',')] if m.group(2) else []
            classes.append({"name": name, "bases": bases})

        functions = []
        # Swift: func myFunc(label name: Type)
        func_pattern = r'func\s+([A-Za-z_]\w*)\s*(?:<[^>]+>)?\s*\(([^)]*)\)'
        for m in re.finditer(func_pattern, content):
            name = m.group(1)
            # Args parsing is complex in Swift, keeping it simple
            args_raw = m.group(2)
            args = []
            if args_raw:
                # Naive split
                args = [a.strip().split(':')[0].strip() for a in args_raw.split(',')]
            functions.append({"name": name, "args": args, "type": "Function"})

        calls = []
        call_pattern = r'([A-Za-z_]\w*)\s*\('
        for m in re.finditer(call_pattern, content):
            if m.group(1) not in ["if", "for", "while", "switch", "guard"]:
                calls.append(m.group(1))

        return {
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "calls": list(set(calls))
        }
