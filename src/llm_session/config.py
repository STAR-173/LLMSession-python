import os
from typing import Optional

class Config:
    """Configuration handler for LLM Automator."""
    
    @staticmethod
    def get_credentials(provider: str) -> dict:
        """
        Retrieve credentials for a specific provider from environment variables.
        
        Args:
            provider: The name of the provider (e.g., 'chatgpt', 'aistudio').
            
        Returns:
            dict: A dictionary containing credentials.
        """
        provider = provider.lower()
        
        if provider == "chatgpt":
            return {
                "email": os.environ.get("CHATGPT_EMAIL") or os.environ.get("LLM_EMAIL"),
                "password": os.environ.get("CHATGPT_PASSWORD") or os.environ.get("LLM_PASSWORD"),
                "google_login": os.environ.get("CHATGPT_GOOGLE_LOGIN", "false").lower() == "true",
                "method": os.environ.get("LLM_METHOD", "email")
            }
        elif provider == "aistudio":
            return {
                "email": os.environ.get("AISTUDIO_EMAIL") or os.environ.get("LLM_EMAIL"),
                "password": os.environ.get("AISTUDIO_PASSWORD") or os.environ.get("LLM_PASSWORD"),
                "method": "google"
            }
        return {}

    @staticmethod
    def get_headless_mode() -> bool:
        """Check if headless mode is enabled (default: False for debug, True for prod)."""
        return os.environ.get("LLM_AUTOMATOR_HEADLESS", "true").lower() == "true"
