from typing import Any, Dict, List, Optional, Union, Type
from utils.logger import logger

class BaseNode:
    """
    Base class for all nodes in the system.
    Inspired by ComfyUI's node structure.
    """
    
    # Metadata definitions
    CATEGORY: str = "Uncategorized"
    FUNCTION: str = "execute"
    OUTPUT_NODE: bool = False
    
    def __init__(self, node_id: str, **kwargs):
        self.id = node_id
        self.inputs: Dict[str, Any] = {}
        self.params: Dict[str, Any] = kwargs.get("params", {})
        self.outputs: Dict[int, Any] = {}
        self._is_changed = False

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        Define input types.
        Example:
        return {
            "required": {"image": ("IMAGE",), "value": ("INT", {"default": 0})}
        }
        """
        return {"required": {}}

    @classmethod
    def RETURN_TYPES(cls) ->  Union[tuple, list]:
        """
        Define return types.
        Example: ("IMAGE", "MASK")
        """
        return ()

    def set_input(self, name: str, data: Any):
        self.inputs[name] = data

    def get_output(self, index: int) -> Any:
        return self.outputs.get(index)

    def execute(self, **kwargs) -> Union[tuple, list, Any]:
        """
        Execute the node logic.
        kwargs will contain inputs matched by name.
        """
        raise NotImplementedError

    def validate_inputs(self) -> bool:
        """
        Check if required inputs are present.
        """
        req = self.INPUT_TYPES().get("required", {})
        for name in req:
            if name not in self.inputs and name not in self.params:
                # Params can serve as default inputs
                return False
        return True

class NodeRegistry:
    _nodes: Dict[str, Type[BaseNode]] = {}

    @classmethod
    def register(cls, node_type: str, node_class: Type[BaseNode]):
        cls._nodes[node_type] = node_class
        logger.info(f"Registered node type: {node_type}")

    @classmethod
    def create(cls, node_type: str, **kwargs) -> Optional[BaseNode]:
        node_class = cls._nodes.get(node_type)
        if node_class:
            return node_class(**kwargs)
        return None

    @classmethod
    def get_class(cls, node_type: str) -> Optional[Type[BaseNode]]:
        return cls._nodes.get(node_type)

    @classmethod
    def get_all_types(cls) -> List[str]:
        return list(cls._nodes.keys())
