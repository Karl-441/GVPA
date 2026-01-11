import os
import yaml
from utils.logger import logger

class ConfigManager:
    _instance = None
    _config = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.load_config()
        return cls._instance

    def load_config(self):
        """Load configuration from files"""
        config_dir = os.path.join(os.getcwd(), 'config')
        if not os.path.exists(config_dir):
            logger.warning(f"Config directory not found: {config_dir}")
            return

        for filename in os.listdir(config_dir):
            if filename.endswith('.yaml') or filename.endswith('.yml'):
                filepath = os.path.join(config_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                        if config_data:
                            self._config.update(config_data)
                            logger.info(f"Loaded config: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load config {filename}: {e}")

    def get(self, key, default=None):
        """Get configuration value"""
        return self._config.get(key, default)

    def set(self, key, value):
        """Set configuration value"""
        self._config[key] = value

config_manager = ConfigManager()
