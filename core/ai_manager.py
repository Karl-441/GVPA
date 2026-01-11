import os
import json
import requests
from utils.logger import logger
from core.options_manager import options_manager

class AIManager:
    def __init__(self):
        self.reload_config()
        # Register observer for real-time updates
        if hasattr(options_manager, "add_observer"):
            options_manager.add_observer(self.reload_config)

    def reload_config(self, settings=None):
        self.provider = options_manager.settings.get("ai_provider", "openai")
        self.api_key = options_manager.settings.get("ai_api_key", os.environ.get("OPENAI_API_KEY", ""))
        self.base_url = options_manager.settings.get("ai_base_url", "https://api.openai.com/v1")
        self.model = options_manager.settings.get("ai_model", "gpt-3.5-turbo")

    def analyze_implicit_dependencies(self, file_content, file_path):
        """
        Ask AI to identify implicit dependencies in the code.
        Returns a list of relation dicts.
        """
        prompt = f"""
        You are a code analysis expert. Analyze the following code file ({file_path}) and identify implicit dependencies that static analysis might miss.
        Focus on:
        1. Message Queue Topics (Publish/Subscribe)
        2. Dynamic/Reflection calls
        3. External API URLs hardcoded in strings
        4. Database table names in raw SQL
        
        Return ONLY a JSON object with a list of relations. Format:
        {{
            "relations": [
                {{ "source": "{os.path.basename(file_path)}", "target": "TargetName", "type": "mq_pub/mq_sub/api_call/db_access", "details": "Topic/URL" }}
            ]
        }}
        
        Code Content:
        {file_content[:3000]} # Truncated to avoid token limits
        """
        
        try:
            res_dict = {}
            if self.provider == "ollama":
                res_dict = self._call_ollama(prompt)
            else:
                res_dict = self._call_openai(prompt)
            
            return res_dict.get("relations", [])
        except Exception as e:
            logger.error(f"AI Analysis failed: {e}")
            return []

    def _call_openai(self, prompt):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful code analyzer. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1
        }
        
        try:
            response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return self._parse_json(content)
        except Exception as e:
            logger.error(f"OpenAI Call Error: {e}")
            return {}

    def _call_ollama(self, prompt):
        # Assumes Ollama is running locally
        url = f"{self.base_url}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            return self._parse_json(result["response"])
        except Exception as e:
            logger.error(f"Ollama Call Error: {e}")
            return {}

    def query_graph(self, graph_data, user_query):
        """
        Natural Language Query for the Graph.
        Returns a dict with "node_titles" or other keys.
        """
        # Simplify graph data for AI prompt
        nodes_summary = []
        for n in graph_data.get("nodes", []):
            nodes_summary.append(f"{n['title']} ({n.get('type', '')})")
            
        prompt = f"""
        You are an architecture assistant. 
        User Query: "{user_query}"
        
        Given the following list of nodes in the project graph:
        {json.dumps(nodes_summary[:1000], indent=2)} # Truncated
        
        Identify which nodes are relevant to the query.
        Return ONLY a JSON object with a list of "node_titles" (use exact titles from list).
        {{ "node_titles": ["api_login", "db_connect"] }}
        """
        
        try:
            if self.provider == "ollama":
                res = self._call_ollama(prompt)
            else:
                res = self._call_openai(prompt)
            
            return res
            
        except Exception as e:
            logger.error(f"AI Query failed: {e}")
            return {}

    def _parse_json(self, text):
        try:
            # Try to find JSON block
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end != -1:
                json_str = text[start:end]
                data = json.loads(json_str)
                return data
            return {}
        except json.JSONDecodeError:
            logger.error("Failed to parse AI response as JSON")
            return {}

ai_manager = AIManager()
