from typing import Dict, Any
import os
import requests
from core.logger import get_logger

logger = get_logger(__name__)

class LocalModel:
    def __init__(self):
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.getenv("MODEL_NAME", "codellama")
    
    def generate_suggestions(self, file: Dict, context: Dict) -> list:
        """Generate code improvement suggestions."""
        try:
            response = self._query_model({
                "code": file["content"],
                "context": context,
                "task": "suggest_improvements"
            })
            return self._parse_suggestions(response)
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return []
    
    def generate_changes(self, analysis: Dict, context: Dict) -> Dict:
        """Generate specific code changes."""
        try:
            response = self._query_model({
                "analysis": analysis,
                "context": context,
                "task": "generate_changes"
            })
            return self._parse_changes(response)
        except Exception as e:
            logger.error(f"Error generating changes: {e}")
            return {}
    
    def _query_model(self, payload: Dict) -> Dict[str, Any]:
        """Send a query to the local LLM."""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": self._format_prompt(payload)
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error querying model: {e}")
            raise
    
    def _format_prompt(self, payload: Dict) -> str:
        """Format the prompt for the model."""
        # Add prompt formatting logic here
        return ""
    
    def _parse_suggestions(self, response: Dict) -> list:
        """Parse model response into a list of suggestions."""
        # Add suggestion parsing logic here
        return []
    
    def _parse_changes(self, response: Dict) -> Dict:
        """Parse model response into a changes dictionary."""
        # Add changes parsing logic here
        return {}
