from utils.logger import logger

class CodeGenerator:
    def __init__(self):
        pass

    def generate_code(self, template, params):
        """
        Generate code from template and parameters
        template: dict with 'code' field
        params: dict of parameters to fill
        """
        try:
            code_template = template.get('code', '')
            # Simple string formatting
            # In a real scenario, use jinja2 for complex templates
            code = code_template.format(**params)
            return code
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return ""

    def generate_function(self, name, args, body, doc="", decorators=None):
        """
        Generate a PEP8 compliant Python function.
        """
        try:
            code = ""
            # Decorators
            if decorators:
                for dec in decorators:
                    code += f"@{dec}\n"
            
            # Signature
            args_str = ", ".join(args)
            code += f"def {name}({args_str}):\n"
            
            # Docstring
            if doc:
                # Handle multi-line docstrings
                if "\n" in doc:
                    code += f'    """\n    {doc}\n    """\n'
                else:
                    code += f'    """{doc}"""\n'
            
            # Body
            if not body:
                code += "    pass\n"
            else:
                for line in body.split('\n'):
                    code += f"    {line}\n"
                    
            return code
        except Exception as e:
            logger.error(f"Error generating function: {e}")
            return ""

code_generator = CodeGenerator()
