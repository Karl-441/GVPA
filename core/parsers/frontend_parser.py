import re
from .base_parser import BaseParser

class FrontendParser(BaseParser):
    def parse(self, file_path, content):
        imports = []
        functions = []
        calls = []
        
        # 1. Pre-processing for Vue files: Extract script content
        script_content = content
        if file_path.endswith('.vue'):
            # Try to find <script setup> or <script>
            script_match = re.search(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
            if script_match:
                script_content = script_match.group(1)
            else:
                # Fallback: if no script tag, might be a template-only component, but usually has script
                pass

        # 2. Parse Imports (ES6 import / CommonJS require)
        # import ... from '...'
        for m in re.finditer(r'import\s+(?:[\w\s{},*]+)\s+from\s+[\'"]([^\'"]+)[\'"]', script_content):
             imports.append(m.group(1))
        # import '...'
        for m in re.finditer(r'import\s+[\'"]([^\'"]+)[\'"]', script_content):
             imports.append(m.group(1))
        # require('...')
        for m in re.finditer(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', script_content):
            imports.append(m.group(1))

        # 3. Parse Functions
        # function foo() {}
        for m in re.finditer(r'function\s+([A-Za-z_]\w*)\s*\(([^)]*)\)', script_content):
            args = [a.strip() for a in m.group(2).split(',') if a.strip()]
            functions.append({"name": m.group(1), "args": args, "type": "Function"})
        # const foo = () => {}
        for m in re.finditer(r'const\s+([A-Za-z_]\w*)\s*=\s*(?:async\s*)?(?:\(([^)]*)\)|(\w+))\s*=>', script_content):
            args_raw = m.group(2) or m.group(3) or ""
            args = [a.strip() for a in args_raw.split(',') if a.strip()]
            functions.append({"name": m.group(1), "args": args, "type": "ArrowFunction"})
        
        # 4. Parse API Calls (axios, fetch)
        # axios.get('/api/xxx')
        api_pattern = r'(?:axios|http|request)\.(get|post|put|delete|patch)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
        for m in re.finditer(api_pattern, script_content):
            method = m.group(1)
            url = m.group(2)
            calls.append(f"API:{method.upper()} {url}")
            
        # fetch('/api/xxx')
        fetch_pattern = r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
        for m in re.finditer(fetch_pattern, script_content):
            calls.append(f"API:FETCH {m.group(1)}")

        # 5. Parse Router Configuration (router/index.js or similar)
        # path: '/user', component: User
        if 'router' in file_path.lower() or 'routes' in file_path.lower():
             route_pattern = r'path\s*:\s*[\'"]([^\'"]+)[\'"]'
             for m in re.finditer(route_pattern, script_content):
                 calls.append(f"ROUTE:{m.group(1)}")

        return {
            "imports": imports,
            "classes": [],
            "functions": functions,
            "calls": list(set(calls))
        }
