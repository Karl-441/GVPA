import requests
import json
import os
from utils.logger import logger
from core.options_manager import options_manager

class LocalLLMBridge:
    """
    Bridge to interact with a locally deployed quantized LLM (e.g., ChatGLM-6B, LLaMA-2).
    Assumes an OpenAI-compatible API or a simple completions endpoint running locally.
    Uses GVPA Options Manager for configuration.
    """
    
    def __init__(self):
        self.timeout = 30  # seconds

    @property
    def api_url(self):
        # Default to localhost if not set
        base = options_manager.settings.get("ai_base_url", "http://localhost:8000/v1")
        if not base.endswith("/chat/completions"):
            # If base is just the root, append the standard endpoint
            # But standard OpenAI base is "v1", and endpoint is "chat/completions"
            # If user enters "http://localhost:8000/v1", we append "/chat/completions"
            if not base.endswith("/"):
                base += "/"
            return base + "chat/completions"
        return base

    @property
    def model(self):
        return options_manager.settings.get("ai_model", "chatglm-6b")

    def is_available(self):
        """Check if the local LLM service is reachable."""
        try:
            # Try to hit the models endpoint or just root
            base = options_manager.settings.get("ai_base_url", "http://localhost:8000/v1")
            url = base.replace("/v1", "/v1/models") # heuristic
            if "localhost" in url:
                resp = requests.get(url, timeout=2)
                return resp.status_code == 200
            return True # Assume remote is available if configured
        except:
            return False

    def chat_completion(self, messages, temperature=0.7):
        """
        Send a chat completion request to the local LLM.
        :param messages: List of {"role": "...", "content": "..."}
        :return: String response or None on failure.
        """
        url = self.api_url
        if not url:
            return None
            
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024
        }
        
        # Add API Key if present
        headers = {"Content-Type": "application/json"}
        api_key = options_manager.settings.get("ai_api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Local LLM Request Failed: {e}")
            return None

    def analyze_code_snippet(self, code_snippet, task="explain"):
        """
        Helper for code analysis tasks.
        """
        prompt = ""
        if task == "dependency":
            prompt = "Analyze the following code and list all external dependencies and dynamic calls. Return JSON format."
        elif task == "risk":
            prompt = "Analyze the following code for security risks or performance issues. Return JSON format."
            
        messages = [
            {"role": "system", "content": "You are a code analysis assistant. Output valid JSON only."},
            {"role": "user", "content": f"{prompt}\n\nCode:\n{code_snippet}"}
        ]
        
        return self.chat_completion(messages)

# Singleton instance
llm_client = LocalLLMBridge()
