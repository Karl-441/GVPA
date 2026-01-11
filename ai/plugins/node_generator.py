from ai.plugin_manager import AIPlugin, AIPluginRegistry
from ai.llm_bridge import llm_client
import os

class NodeGenAction(AIPlugin):
    def __init__(self):
        super().__init__()
        self.name = "Smart Node Generator"
        self.description = "Generates new Node class code based on requirements."
        self.version = "1.0"
        
        self.template = """
from core.nodes.base_node import BaseNode
from core.sockets import InputSocket, OutputSocket
import cv2
import numpy as np

class {class_name}(BaseNode):
    def __init__(self):
        super().__init__()
        self.name = "{node_name}"
        self.add_input(InputSocket("image", "Image"))
        self.add_output(OutputSocket("image", "Image"))
    
    def execute(self, inputs):
        img = inputs.get("image")
        if img is None:
            return None
            
        # Implementation: {description}
        # TODO: Add logic here
        
        return {"image": img}
"""

    def execute(self, context):
        """
        Context:
        - 'description': str
        - 'output_path': str (directory to save)
        - 'use_llm': bool
        """
        description = context.get("description", "Custom Node")
        output_path = context.get("output_path", ".")
        use_llm = context.get("use_llm", False)
        
        class_name = "".join(x.title() for x in description.split()) + "Node"
        class_name = ''.join(e for e in class_name if e.isalnum())
        
        code = ""
        
        if use_llm and llm_client.is_available():
            prompt = f"""
            Create a Python class for a GVPA Node named '{class_name}'.
            It should inherit from BaseNode.
            Requirement: {description}.
            Use OpenCV if needed.
            Output only the code.
            """
            generated = llm_client.chat_completion([
                {"role": "system", "content": "You are a Python expert writing plugin nodes for GVPA."},
                {"role": "user", "content": prompt}
            ])
            if generated:
                code = generated.replace("```python", "").replace("```", "")
        
        if not code:
            # Fallback to template
            code = self.template.format(
                class_name=class_name,
                node_name=description,
                description=description
            )
            
        # Save file
        filename = f"node_{class_name.lower()}.py"
        full_path = os.path.join(output_path, filename)
        
        try:
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code)
            return {"status": "success", "file_path": full_path, "code": code}
        except Exception as e:
            return {"status": "error", "message": str(e)}

AIPluginRegistry.register(NodeGenAction)
