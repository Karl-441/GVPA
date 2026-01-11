import os
from utils.logger import logger
from core.parsers.python_parser import PythonParser
from core.parsers.java_parser import JavaParser
from core.parsers.cpp_parser import CppParser
from core.parsers.go_parser import GoParser
from core.parsers.rust_parser import RustParser
from core.parsers.kotlin_parser import KotlinParser
from core.parsers.frontend_parser import FrontendParser
from core.parsers.dockerfile_parser import DockerfileParser
from core.parsers.yaml_parser import YAMLParser
from core.parsers.json_parser import JSONParser
from core.parsers.xml_parser import XMLParser
from core.parsers.sql_parser import SQLParser
from core.parsers.csharp_parser import CSharpParser
from core.parsers.swift_parser import SwiftParser
from core.parsers.objc_parser import ObjCParser

class CodeAnalyzer:
    def __init__(self):
        self.parsers = {
            ".py": PythonParser(),
            ".java": JavaParser(),
            ".cpp": CppParser(),
            ".h": CppParser(),
            ".hpp": CppParser(),
            ".go": GoParser(),
            ".rs": RustParser(),
            ".kt": KotlinParser(),
            ".js": FrontendParser(),
            ".ts": FrontendParser(),
            ".jsx": FrontendParser(),
            ".tsx": FrontendParser(),
            ".vue": FrontendParser(),
            ".cs": CSharpParser(),
            ".swift": SwiftParser(),
            ".m": ObjCParser(),
            ".mm": ObjCParser(),
            ".yml": YAMLParser(),
            ".yaml": YAMLParser(),
            ".json": JSONParser(),
            ".xml": XMLParser(),
            ".sql": SQLParser()
        }

    def analyze_file(self, file_path):
        """
        Analyze a source file and return its structure.
        """
        base = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower()
        parser = self.parsers.get(ext)
        if not parser and base.lower() == "dockerfile":
            parser = DockerfileParser()
        
        if not parser:
            return None

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return parser.parse(file_path, content)
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return None

code_analyzer = CodeAnalyzer()
