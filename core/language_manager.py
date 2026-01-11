import json
import os
from utils.logger import logger

class LanguageManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LanguageManager, cls).__new__(cls)
            cls._instance.current_lang = "en"
            cls._instance.translations = {}
            cls._instance.observers = []
            cls._instance.load_languages()
        return cls._instance

    def load_languages(self):
        """Load language files from data/i18n"""
        base_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'i18n')
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
            return

        for filename in os.listdir(base_dir):
            if filename.endswith('.json'):
                lang_code = filename.split('.')[0]
                try:
                    with open(os.path.join(base_dir, filename), 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to load language {filename}: {e}")

    def set_language(self, lang_code):
        if lang_code in self.translations:
            self.current_lang = lang_code
            self.notify_observers()
            return True
        return False

    def get(self, key_path):
        """
        Get translation by key path (e.g. "tabs.structure")
        """
        keys = key_path.split('.')
        value = self.translations.get(self.current_lang, {})
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return key_path # Not found or invalid structure
        
        return value if value is not None else key_path

    def add_observer(self, observer_method):
        """Register a method to be called when language changes"""
        self.observers.append(observer_method)

    def notify_observers(self):
        for observer in self.observers:
            try:
                observer()
            except Exception as e:
                logger.error(f"Error notifying observer: {e}")

lang_manager = LanguageManager()
