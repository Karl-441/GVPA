import re
from .base_parser import BaseParser

class CSharpParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        # C#: using System.IO;
        for m in re.finditer(r'^\s*using\s+([\w\.]+);', content, re.M):
            imports.append(m.group(1))

        classes = []
        # C#: public class MyClass : BaseClass
        class_pattern = r'(?:public|private|internal|protected)?\s*(?:static|sealed|abstract|partial)?\s*class\s+([A-Za-z_]\w*)(?:\s*:\s*([A-Za-z_][\w\.,\s]*))?'
        for m in re.finditer(class_pattern, content):
            name = m.group(1)
            bases = [b.strip() for b in m.group(2).split(',')] if m.group(2) else []
            classes.append({"name": name, "bases": bases})

        functions = []
        # C#: public void MyFunc(int a)
        # Simplified regex for methods
        method_pattern = r'(?:public|private|internal|protected)\s+(?:static\s+)?(?:virtual\s+|override\s+|abstract\s+)?[\w\.<>\[\]]+\s+([A-Za-z_]\w*)\s*\(([^)]*)\)'
        for m in re.finditer(method_pattern, content):
            name = m.group(1)
            args = [a.strip().split(' ')[-1] for a in m.group(2).split(',') if a.strip()] # Extract arg name
            functions.append({"name": name, "args": args, "type": "Method"})

        # Calls (rough approximation)
        calls = []
        call_pattern = r'([A-Za-z_]\w*)\s*\('
        for m in re.finditer(call_pattern, content):
            if m.group(1) not in ["if", "for", "while", "switch", "catch", "using"]:
                calls.append(m.group(1))

        return {
            "imports": imports,
            "classes": classes,
            "functions": functions,
            "calls": list(set(calls))
        }
