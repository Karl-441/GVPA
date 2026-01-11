import cv2
import numpy as np
from utils.logger import logger

class NodeRegistry:
    _nodes = {}

    @classmethod
    def register(cls, node_type, node_class):
        cls._nodes[node_type] = node_class

    @classmethod
    def create(cls, node_type, **kwargs):
        node_class = cls._nodes.get(node_type)
        if node_class:
            return node_class(**kwargs)
        # Fallback for dynamic nodes (Function/Method)
        if node_type not in cls._nodes and "Function" in cls._nodes:
             # If type matches a known function node convention, or we treat unknown as generic function
             # For now, let's assume CodeGraphBuilder sets title to Function Name.
             # But execution engine looks up by title.
             # We can register a "GenericFunction" and use that if specific type not found?
             # Better: ExecutionEngine should handle mapping.
             # Here we return GenericFunctionNode if registered and type looks like a function name
             return cls._nodes["GenericFunction"](**kwargs)
        return None

    @classmethod
    def get_all_types(cls):
        return list(cls._nodes.keys())

class BaseNode:
    def __init__(self, node_id, **kwargs):
        self.id = node_id
        self.inputs = {}  # socket_index -> data
        self.params = kwargs.get("params", {})
        self.outputs = {} # socket_index -> data

    def set_input(self, index, data):
        self.inputs[index] = data

    def get_output(self, index):
        return self.outputs.get(index)

    def execute(self):
        raise NotImplementedError

# --- Generic Python Function Node ---
class GenericFunctionNode(BaseNode):
    """
    Executes a Python function dynamically.
    Params: func_name, module_path (optional)
    """
    def execute(self):
        func_name = self.params.get("func_name")
        if not func_name:
            logger.warning(f"Node {self.id}: No function name specified")
            return

        # In a real scenario, we would import the module dynamically.
        # For this prototype, we mock execution or print trace.
        logger.info(f"Executing Generic Function: {func_name}")
        
        # Mock logic: Pass input 0 to output 0
        input_data = self.inputs.get(0)
        if input_data is not None:
            self.outputs[0] = input_data
            logger.info(f"  Passed data through {func_name}")
        else:
            self.outputs[0] = "Result from " + func_name

# --- OpenCV Nodes ---

class ImageReadNode(BaseNode):
    """
    Params: file_path
    Outputs: 0: image
    """
    def execute(self):
        path = self.params.get("file_path", "")
        if not path:
            logger.warning(f"Node {self.id}: No file path specified")
            self.outputs[0] = None
            return

        try:
            img = cv2.imread(path)
            if img is None:
                logger.error(f"Node {self.id}: Failed to load image {path}")
            self.outputs[0] = img
        except Exception as e:
            logger.error(f"Node {self.id}: Error reading image: {e}")
            self.outputs[0] = None

class CvtColorNode(BaseNode):
    """
    Inputs: 0: image
    Params: code (e.g., cv2.COLOR_BGR2GRAY)
    Outputs: 0: image
    """
    def execute(self):
        img = self.inputs.get(0)
        if img is None:
            return

        code = self.params.get("code", cv2.COLOR_BGR2GRAY)
        try:
            # Handle string input for code if necessary, for now assume int or registered constant name
            if isinstance(code, str):
                code = getattr(cv2, code, cv2.COLOR_BGR2GRAY)
            
            res = cv2.cvtColor(img, int(code))
            self.outputs[0] = res
        except Exception as e:
            logger.error(f"Node {self.id}: Convert color error: {e}")

class GaussianBlurNode(BaseNode):
    """
    Inputs: 0: image
    Params: ksize (int, default 5)
    Outputs: 0: image
    """
    def execute(self):
        img = self.inputs.get(0)
        if img is None:
            return

        ksize = int(self.params.get("ksize", 5))
        if ksize % 2 == 0: ksize += 1 # Ensure odd
        
        try:
            res = cv2.GaussianBlur(img, (ksize, ksize), 0)
            self.outputs[0] = res
        except Exception as e:
            logger.error(f"Node {self.id}: Blur error: {e}")

class CannyNode(BaseNode):
    """
    Inputs: 0: image
    Params: threshold1, threshold2
    Outputs: 0: image
    """
    def execute(self):
        img = self.inputs.get(0)
        if img is None:
            return
            
        t1 = float(self.params.get("threshold1", 100))
        t2 = float(self.params.get("threshold2", 200))
        
        try:
            res = cv2.Canny(img, t1, t2)
            self.outputs[0] = res
        except Exception as e:
            logger.error(f"Node {self.id}: Canny error: {e}")

class ImageShowNode(BaseNode):
    """
    Inputs: 0: image
    Params: window_name
    """
    def execute(self):
        img = self.inputs.get(0)
        if img is None:
            logger.warning(f"Node {self.id}: No input image to show")
            return

        name = self.params.get("window_name", f"Result {self.id}")
        try:
            cv2.imshow(name, img)
            # We rely on main loop or explicit waitKey elsewhere, 
            # but for a quick tool, a small waitKey might be needed to refresh buffer
            cv2.waitKey(1) 
        except Exception as e:
            logger.error(f"Node {self.id}: Show error: {e}")

# Register Nodes
NodeRegistry.register("GenericFunction", GenericFunctionNode)
NodeRegistry.register("Read Image", ImageReadNode)
NodeRegistry.register("Convert Color", CvtColorNode)
NodeRegistry.register("Gaussian Blur", GaussianBlurNode)
NodeRegistry.register("Canny Edge", CannyNode)
NodeRegistry.register("Show Image", ImageShowNode)
