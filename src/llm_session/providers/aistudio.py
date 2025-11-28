import time
import logging
from typing import Optional, Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from .base import LLMProvider
from ..exceptions import AuthenticationError, SelectorError, PromptError, OTPRequiredError

logger = logging.getLogger(__name__)

class GoogleAIStudioProvider(LLMProvider):
    """Google AI Studio (Gemini) implementation."""

    URL = "https://aistudio.google.com/prompts/new_chat"

    # Default Selectors adapted for robustness
    DEFAULT_SELECTORS = {
        # Landmarks for auth check
        "main_landmark": "ms-chunk-editor",
        
        # Google Login Flow
        "email_input": 'input[type="email"]',
        "email_next": 'button:has-text("Next")',
        "password_input": 'input[type="password"]',
        "password_next": 'button:has-text("Next")',
        
        # Editor Interaction
        "textarea": 'textarea[aria-label*="prompt"]',
        "run_button": 'button[aria-label="Run"]',
        "stoppable_button": 'button[aria-label="Run"].stoppable',
        
        # Response Extraction
        "response_block": "ms-chat-turn",
        "more_options_btn": "button[aria-label='Open options']",
        "copy_menu_item": "[role='menuitem']:has-text('Copy')",
        
        # Dialogs
        "save_drive_cancel": "button:has-text('Cancel and use Temporary chat')"
    }

    def __init__(self, page: Page, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        super().__init__(page)
        self.config = config or {}
        self.on_otp_required = on_otp_required
        self.selectors = self.DEFAULT_SELECTORS.copy()
        
        if "selectors" in self.config:
            self.selectors.update(self.config["selectors"])
            
        # Mapped for Automator's generic auth check
        self.SEL_PROFILE_BTN = self.selectors["main_landmark"]

    def login(self, credentials: dict) -> bool:
        """
        Attempts to log in to Google AI Studio.
        """
        logger.info("Starting AI Studio login process...")
        
        try:
            self.page.goto(self.URL, wait_until="domcontentloaded")
            
            # Check if already logged in
            try:
                self.page.wait_for_selector(self.selectors["main_landmark"], timeout=5000)
                logger.info("Already logged in.")
                return True
            except:
                pass

            # Attempt Login Flow
            email = credentials.get("email")
            password = credentials.get("password")

            if not email or not password:
                raise AuthenticationError("Email and password required for login.")

            # Look for a sign-in redirect or button
            # Usually AI Studio redirects to accounts.google.com automatically if not logged in
            logger.info("Attempting Google Authentication...")

            # 1. Email
            try:
                self.page.wait_for_selector(self.selectors["email_input"], timeout=10000)
                logger.info("Entering email...")
                self.page.fill(self.selectors["email_input"], email)
                self.page.click(self.selectors["email_next"])
            except Exception as e:
                raise SelectorError(f"Could not find email input or login flow started incorrectly: {e}")

            # 2. Password
            try:
                logger.info("Entering password...")
                self.page.wait_for_selector(self.selectors["password_input"], state="visible", timeout=10000)
                self.page.fill(self.selectors["password_input"], password)
                self.page.click(self.selectors["password_next"])
            except Exception as e:
                raise SelectorError(f"Could not find password input: {e}")

            # 3. Wait for success
            logger.info("Waiting for authentication...")
            try:
                # Check for OTP or Success
                self.page.wait_for_selector(self.selectors["main_landmark"], timeout=30000)
                logger.info("Login successful.")
                return True
            except PlaywrightTimeoutError:
                 raise AuthenticationError("Login timed out. OTP or 2FA might be required.")

        except Exception as e:
            logger.error(f"Login failed: {e}")
            raise AuthenticationError(f"Login failed: {e}")

    def handle_dialogs(self):
        """Handle specific AI Studio dialogs (e.g. Save to Drive)."""
        try:
            # Check for 'Save to Drive' post-prompt dialog
            if self.page.is_visible(self.selectors["save_drive_cancel"]):
                logger.info("Dismissing 'Save to Drive' dialog...")
                self.page.click(self.selectors["save_drive_cancel"])
                self.page.wait_for_selector(self.selectors["save_drive_cancel"], state="hidden")
        except:
            pass

    def send_prompt(self, prompt: str) -> str:
        self.handle_dialogs()
        
        try:
            # 1. Input Prompt
            # Use JS Injection for speed/compatibility with ms-chunk-editor
            logger.info("Injecting prompt via JS...")
            
            textarea_loc = self.page.locator(self.selectors["textarea"])
            expect(textarea_loc).to_be_visible()
            
            textarea_handle = textarea_loc.element_handle()
            
            self.page.evaluate(
                """
                ({ element, text }) => {
                    element.value = text;
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                }
                """,
                { 'element': textarea_handle, 'text': prompt }
            )
            
            # 2. Click Run
            run_btn = self.page.locator(self.selectors["run_button"])
            expect(run_btn).to_be_enabled()
            run_btn.click()
            
        except Exception as e:
            raise PromptError(f"Failed to send prompt: {e}")
            
        # 3. Wait for Generation
        logger.info("Waiting for response generation...")
        try:
            # Wait for button to become stoppable (generation started)
            self.page.wait_for_selector(self.selectors["stoppable_button"], timeout=10000)
            # Wait for button to stop being stoppable (generation finished)
            self.page.wait_for_selector(self.selectors["stoppable_button"], state="hidden", timeout=120000)
        except PlaywrightTimeoutError:
            raise PromptError("Timeout waiting for response generation.")

        # 4. Extract Response via Clipboard
        try:
            # Handle post-turn dialogs (like First Run "Save to Drive" check)
            self.handle_dialogs()
            
            logger.info("Extracting response via clipboard...")
            
            # Get the last response block
            response_blocks = self.page.locator(self.selectors["response_block"])
            last_block = response_blocks.last
            expect(last_block).to_be_visible()
            
            # Hover to show options
            last_block.hover()
            self.page.wait_for_timeout(500)
            
            # Click More Options
            # Sometimes the button is only visible on hover
            more_opts = last_block.locator(self.selectors["more_options_btn"])
            more_opts.click()
            
            # Click Copy
            copy_btn = self.page.locator(self.selectors["copy_menu_item"]).last
            copy_btn.click()
            
            # Read Clipboard
            clipboard_text = self.page.evaluate("async () => await navigator.clipboard.readText()")
            if not clipboard_text:
                return ""
            return clipboard_text.strip()
            
        except Exception as e:
            raise PromptError(f"Failed to extract response: {e}")
