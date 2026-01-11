import os
import json
from utils.logger import logger

class TemplateManager:
    def __init__(self):
        self.templates_dir = os.path.join(os.getcwd(), 'gvpa', 'data', 'templates')
        self.templates = {}
        self.load_templates()

    def load_templates(self):
        """Load all templates from JSON files"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            return

        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                path = os.path.join(self.templates_dir, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                        self.templates[template.get('name', filename)] = template
                except Exception as e:
                    logger.error(f"Failed to load template {filename}: {e}")

    def get_template(self, name):
        return self.templates.get(name)

    def get_all_templates(self):
        return self.templates

template_manager = TemplateManager()
