from abc import ABC, abstractmethod
from utils.logger import logger

class AIPlugin(ABC):
    """Base class for all AI Plugins"""
    
    def __init__(self):
        self.name = "Base Plugin"
        self.description = "Base AI Plugin"
        self.version = "1.0"
        self.enabled = True

    @abstractmethod
    def execute(self, context):
        """
        Execute the plugin logic.
        :param context: A dictionary containing 'graph_data', 'project_path', etc.
        :return: A dictionary with results (e.g., 'modified_nodes', 'new_edges', 'suggestions')
        """
        pass

class AIPluginRegistry:
    _plugins = {}

    @classmethod
    def register(cls, plugin_class):
        """Register a new plugin class"""
        try:
            plugin = plugin_class()
            cls._plugins[plugin.name] = plugin
            logger.info(f"Registered AI Plugin: {plugin.name}")
        except Exception as e:
            logger.error(f"Failed to register plugin {plugin_class}: {e}")

    @classmethod
    def get_plugin(cls, name):
        return cls._plugins.get(name)

    @classmethod
    def get_all_plugins(cls):
        return list(cls._plugins.values())

    @classmethod
    def execute_plugin(cls, name, context):
        plugin = cls.get_plugin(name)
        if plugin and plugin.enabled:
            logger.info(f"Executing AI Plugin: {name}")
            try:
                return plugin.execute(context)
            except Exception as e:
                logger.error(f"Error executing plugin {name}: {e}")
                return None
        return None
