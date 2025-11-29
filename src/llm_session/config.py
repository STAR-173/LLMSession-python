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
                "email": os.environ.get("CHATGPT_EMAIL") or email,
                "password": os.environ.get("CHATGPT_PASSWORD") or password,
                "google_login": os.environ.get("CHATGPT_GOOGLE_LOGIN", "false").lower() == "true",
                "method": os.environ.get("LLM_METHOD", "email")
            }
        elif provider == "aistudio":
            return {
                "email": os.environ.get("AISTUDIO_EMAIL") or email,
                "password": os.environ.get("AISTUDIO_PASSWORD") or password,
                "method": "google"
            }
        elif provider == "claude":
            return {
                "email": os.environ.get("CLAUDE_EMAIL") or email,
                "password": os.environ.get("CLAUDE_PASSWORD") or password,
                "method": "google"
            }
        return {}

    @staticmethod
    def get_headless_mode() -> bool:
        return os.environ.get("LLM_AUTOMATOR_HEADLESS", "true").lower() == "true"
