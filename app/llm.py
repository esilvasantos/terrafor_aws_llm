import requests
import logging
from config import Config

class LLM:
    @staticmethod
    def ask_ollama(prompt):
        try:
            url = Config.OLLAMA_CONFIG["BASE_URL"]
            payload = {
                "model": Config.OLLAMA_CONFIG["MODEL"],
                "prompt": prompt,
                "stream": False,
                "options": Config.OLLAMA_CONFIG["OPTIONS"]
            }
            
            response = requests.post(url, json=payload, timeout=300)
            logging.debug(f"Received response from Ollama: {response.status_code}")
            
            if response.status_code == 404:
                return "Model not found. Please ensure the model is properly installed."
                
            response.raise_for_status()
            result = response.json()
            return result["response"]
        except Exception as e:
            logging.error(f"Ollama error: {str(e)}")
            return f"Error generating response: {str(e)}"