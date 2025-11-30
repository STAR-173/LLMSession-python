import os
from typing import Optional

class Config:
    """Configuration handler for LLM Automator."""
    
    @staticmethod
    def get_credentials(provider: str) -> dict:
        provider = provider.lower()
        
        # Generic fallback
        email = os.environ.get("LLM_EMAIL")
        password = os.environ.get("LLM_PASSWORD")
        
        if provider == "chatgpt":
            return {
                "email": email,
                "password": password,
                "method": "google"
            }
        elif provider == "aistudio":
            return {
                "email": email,
                "password": password,
                "method": "google"
            }
        elif provider == "claude":
            return {
                "email": email,
                "password": password,
                "method": "google"
            }
        return {}

    @staticmethod
    def get_headless_mode() -> bool:
        return os.environ.get("LLM_AUTOMATOR_HEADLESS", "true").lower() == "true"
