import re
from .base_parser import BaseParser

class ObjCParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        # ObjC: #import "Header.h" or #import <Framework/Framework.h>
        for m in re.finditer(r'^\s*#import\s+["<]([\w\./]+)[">]', content, re.M):
            imports.append(m.group(1))

        classes = []
        # ObjC: @interface MyClass : BaseClass
        class_pattern = r'@interface\s+([A-Za-z_]\w*)(?:\s*:\s*([A-Za-z_]\w*))?'
        for m in re.finditer(class_pattern, content):
            name = m.group(1)
            bases = [m.group(2)] if m.group(2) else []
            classes.append({"name": name, "bases": bases})

        functions = []
        # ObjC: - (void)myMethod:(Type)arg
        method_pattern = r'[-+]\s*\([^)]+\)\s*([A-Za-z_]\w*)'
        for m in re.finditer(method_pattern, content):
            functions.append({"name": m.group(1), "args": [], "type": "Method"})

        calls = []
        # ObjC: [object method] -> rough regex for [ word word ]
        call_pattern = r'\[\s*[A-Za-z_]\w*\s+([A-Za-z_]\w*)\s*\]'
        for m in re.finditer(call_pattern, content):
            calls.append(m.group(1))

        return {
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "calls": list(set(calls))
        }
