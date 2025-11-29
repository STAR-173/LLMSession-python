from typing import List, Optional, Callable, Union
import logging
from .browser import BrowserManager
from .config import Config
from .providers.chatgpt import ChatGPTProvider
from .providers.aistudio import GoogleAIStudioProvider
from .providers.claude import ClaudeProvider
from .exceptions import SetupError, OTPRequiredError

logger = logging.getLogger(__name__)

class Automator:
    """
    Main entry point for the LLM Web Automator.
    """

    def __init__(self, provider: str = "chatgpt", headless: bool = True, credentials: Optional[dict] = None, session_path: Optional[str] = None, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        self.provider_name = provider.lower()
        self.headless = headless
        self.credentials = credentials
        self.session_path = session_path
        self.config = config or {}
        self.on_otp_required = on_otp_required
        self.browser_manager = BrowserManager()
        self.provider = None
        
        # Initialize
        self._setup()

    def _setup(self):
        """Initialize browser and provider."""
        # 1. Start Browser
        page = self.browser_manager.start(headless=self.headless, session_path=self.session_path)
        
        # Grant clipboard permissions
        self.browser_manager.context.grant_permissions(["clipboard-read", "clipboard-write"])
        
        # 2. Initialize Provider
        if self.provider_name == "chatgpt":
            self.provider = ChatGPTProvider(page, config=self.config, on_otp_required=self.on_otp_required)
        elif self.provider_name == "aistudio":
            self.provider = GoogleAIStudioProvider(page, config=self.config, on_otp_required=self.on_otp_required)
        elif self.provider_name == "claude":
            self.provider = ClaudeProvider(page, config=self.config, on_otp_required=self.on_otp_required)
        else:
            raise NotImplementedError(f"Provider {self.provider_name} not supported.")
            
        # 3. Check Auth / Auto-Login
        if not self.browser_manager.is_authenticated(self.provider.URL, self.provider.SEL_PROFILE_BTN):
            logger.info("Not authenticated. Initiating login...")
            
            creds = self.credentials or Config.get_credentials(self.provider_name)
            
            if not creds.get("email"):
                raise SetupError(f"Credentials (email) not found for {self.provider_name}.")
            
            self.provider.login(creds)
            
            if self.session_path:
                self.browser_manager.save_session(self.session_path)
        else:
            logger.info("Session authenticated.")

    def process_prompt(self, prompt: str) -> str:
        if not self.provider:
            raise SetupError("Provider not initialized.")
        return self.provider.send_prompt(prompt)

    def process_chain(self, prompts: List[Union[str, Callable[[str], str]]]) -> List[str]:
        responses = []
        last_response = ""
        
        for i, prompt_item in enumerate(prompts):
            current_prompt = ""
            
            if callable(prompt_item):
                current_prompt = prompt_item(last_response)
            elif isinstance(prompt_item, str):
                if "{{previous}}" in prompt_item:
                     current_prompt = prompt_item.replace("{{previous}}", last_response)
                elif "{}" in prompt_item:
                    try:
                        current_prompt = prompt_item.format(last_response)
                    except ValueError:
                        current_prompt = prompt_item
                elif "{{}}" in prompt_item:
                    current_prompt = prompt_item.replace("{{}}", last_response)
                else:
                    current_prompt = prompt_item
            
            logger.info(f"Processing prompt {i+1}/{len(prompts)}...")
            response = self.process_prompt(current_prompt)
            responses.append(response)
            last_response = response
            
        return responses

    def close(self):
        self.browser_manager.stop()
