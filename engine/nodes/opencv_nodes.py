import cv2
import numpy as np
from utils.logger import logger
from engine.base import BaseNode, NodeRegistry

# --- Generic Python Function Node ---
class GenericFunctionNode(BaseNode):
    """
    Executes a Python function dynamically.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"input_data": ("ANY",)},
            "optional": {"func_name": ("STRING", {"default": ""})}
        }

    @classmethod
    def RETURN_TYPES(cls):
        return ("ANY",)

    def execute(self, input_data=None, func_name=""):
        if not func_name:
            # Fallback to params if not passed as input
            func_name = self.params.get("func_name", "")
            
        if not func_name:
            logger.warning(f"Node {self.id}: No function name specified")
            return input_data

        logger.info(f"Executing Generic Function: {func_name}")
        # Mock logic
        return input_data

# --- OpenCV Nodes ---

class ImageReadNode(BaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {"file_path": ("STRING", {"default": ""})}
        }
    
    @classmethod
    def RETURN_TYPES(cls):
        return ("IMAGE",)

    def execute(self, file_path=""):
        if not file_path:
             file_path = self.params.get("file_path", "")

        if not file_path:
            logger.warning(f"Node {self.id}: No file path specified")
            return None

        try:
            img = cv2.imread(file_path)
            if img is None:
                logger.error(f"Node {self.id}: Failed to load image {file_path}")
            return img
        except Exception as e:
            logger.error(f"Node {self.id}: Error reading image: {e}")
            return None

class CvtColorNode(BaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"image": ("IMAGE",)},
            "optional": {"code": ("INT", {"default": cv2.COLOR_BGR2GRAY})}
        }

    @classmethod
    def RETURN_TYPES(cls):
        return ("IMAGE",)

    def execute(self, image, code=cv2.COLOR_BGR2GRAY):
        if image is None:
            return None
        
        # Check if code is in params
        if "code" in self.params:
            code = self.params["code"]

        try:
            if isinstance(code, str):
                code = getattr(cv2, code, cv2.COLOR_BGR2GRAY)
            
            res = cv2.cvtColor(image, int(code))
            return res
        except Exception as e:
            logger.error(f"Node {self.id}: Convert color error: {e}")
            return None

class GaussianBlurNode(BaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"image": ("IMAGE",)},
            "optional": {"ksize": ("INT", {"default": 5})}
        }

    @classmethod
    def RETURN_TYPES(cls):
        return ("IMAGE",)

    def execute(self, image, ksize=5):
        if image is None:
            return None

        if "ksize" in self.params:
            ksize = int(self.params["ksize"])

        if ksize % 2 == 0: ksize += 1
        
        try:
            res = cv2.GaussianBlur(image, (ksize, ksize), 0)
            return res
        except Exception as e:
            logger.error(f"Node {self.id}: Blur error: {e}")
            return None

class CannyNode(BaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"image": ("IMAGE",)},
            "optional": {
                "threshold1": ("FLOAT", {"default": 100}),
                "threshold2": ("FLOAT", {"default": 200})
            }
        }

    @classmethod
    def RETURN_TYPES(cls):
        return ("IMAGE",)

    def execute(self, image, threshold1=100, threshold2=200):
        if image is None:
            return None
            
        if "threshold1" in self.params:
            threshold1 = float(self.params["threshold1"])
        if "threshold2" in self.params:
            threshold2 = float(self.params["threshold2"])
        
        try:
            res = cv2.Canny(image, threshold1, threshold2)
            return res
        except Exception as e:
            logger.error(f"Node {self.id}: Canny error: {e}")
            return None

class ImageShowNode(BaseNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"image": ("IMAGE",)},
            "optional": {"window_name": ("STRING", {"default": "Result"})}
        }
    
    @classmethod
    def RETURN_TYPES(cls):
        return ()

    def execute(self, image, window_name="Result"):
        if image is None:
            logger.warning(f"Node {self.id}: No input image to show")
            return

        if "window_name" in self.params:
            window_name = self.params["window_name"]
            
        # Use generic name if default
        if window_name == "Result":
            window_name = f"Result {self.id}"

        try:
            cv2.imshow(window_name, image)
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
