import time
import logging
from typing import Optional, Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from .base import LLMProvider
from ..exceptions import AuthenticationError, SelectorError, PromptError, OTPRequiredError

logger = logging.getLogger(__name__)

class ClaudeProvider(LLMProvider):
    """Claude.ai (Anthropic) implementation."""

    URL = "https://claude.ai/new?incognito"

    DEFAULT_SELECTORS = {
        # Auth / Landing
        "login_google_btn": 'button[data-testid="login-with-google"]',
        "user_menu_btn": 'button[data-testid="user-menu-button"]', 
        
        # Google Auth Flow (Inside Popup)
        "email_input": 'input[type="email"]',
        "email_next": 'button:has-text("Next")',
        "password_input": 'input[type="password"]',
        "password_next": 'button:has-text("Next")',
        "account_tile_base": 'div[role="link"][data-identifier]',
        # Generic "Continue" in Google prompts
        "google_continue_btn": 'button:has-text("Continue")', 
        
        # Chat Interface
        "chat_input": 'div[contenteditable="true"][data-testid="chat-input"]',
        "send_btn": 'button[aria-label="Send message"]',
        
        # State Indicators
        "stop_btn": 'button[aria-label="Stop response"]', 
        
        # Response Extraction
        "copy_btn": 'button[data-testid="action-bar-copy"]',
    }

    def __init__(self, page: Page, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        super().__init__(page)
        self.config = config or {}
        self.on_otp_required = on_otp_required
        self.selectors = self.DEFAULT_SELECTORS.copy()
        
        if "selectors" in self.config:
            self.selectors.update(self.config["selectors"])
            
        # We point this to chat_input so Automator knows we aren't ready until input is visible
        self.SEL_PROFILE_BTN = self.selectors["chat_input"]

    def login(self, credentials: dict) -> bool:
        logger.info("Starting Claude login process...")
        email = credentials.get("email")
        password = credentials.get("password")

        # 1. Navigate
        try:
            self.page.goto(self.URL, wait_until="domcontentloaded")
        except:
            pass # Continue to checks

        # 2. FAST CHECK: Are we already ready?
        if self.is_fully_ready():
            logger.info("Already logged in and ready.")
            return True

        # 3. FAST CHECK: Is the Login Button visible? 
        # (Prioritize this over sidebar to avoid waiting on 'ghost' sessions)
        if self.page.is_visible(self.selectors["login_google_btn"]):
            return self._perform_google_login(email, password)

        # 4. Sidebar Check (Only if login button missing)
        if self.page.is_visible(self.selectors["user_menu_btn"]):
            logger.info("Sidebar detected. Waiting for Chat Input...")
            if self.wait_for_chat_input(timeout=5000):
                return True
            logger.warning("Chat input stalled. Reloading...")
            self.page.reload()
            if self.wait_for_chat_input(timeout=5000):
                return True
        
        # 5. Fallback: If we are here, we might be on login page but button didn't load yet
        try:
            self.page.wait_for_selector(self.selectors["login_google_btn"], timeout=5000)
            return self._perform_google_login(email, password)
        except:
            raise AuthenticationError("Could not find Login button and Chat Input is missing.")

    def _perform_google_login(self, email, password):
        """Handles the Google Login Popup Flow."""
        logger.info("Clicking 'Continue with Google' and waiting for popup...")
        
        try:
            # Prepare to catch the popup window
            with self.page.expect_popup() as popup_info:
                self.page.click(self.selectors["login_google_btn"])
            
            popup = popup_info.value
            logger.info("Google Popup opened. Interacting with popup...")
            
            # Wait for popup to load content
            popup.wait_for_load_state("domcontentloaded")
            
            # --- GOOGLE AUTH INSIDE POPUP ---
            
            # A. Check for Account Chooser vs Email Input
            account_selector = f'div[role="link"][data-identifier="{email}"]'
            
            try:
                # Wait for *something* to appear in the popup
                popup.wait_for_selector(f'{self.selectors["email_input"]}, {account_selector}', timeout=5000)
                
                # PATH A: Account Tile (Session remembered)
                if popup.locator(account_selector).is_visible():
                    logger.info(f"Found account tile for {email} in popup. Clicking...")
                    popup.click(account_selector)
                    # Sometimes detection needs a follow-up 'Continue'
                    try:
                        popup.wait_for_selector(self.selectors["google_continue_btn"], timeout=3000)
                        popup.click(self.selectors["google_continue_btn"])
                    except: pass

                # PATH B: Email Input
                else:
                    logger.info("Entering Email in popup...")
                    popup.fill(self.selectors["email_input"], email)
                    popup.click(self.selectors["email_next"])
                    
                    # Password (only if email flow used)
                    if password:
                        try:
                            popup.wait_for_selector(self.selectors["password_input"], state="visible", timeout=5000)
                            logger.info("Entering Password in popup...")
                            popup.fill(self.selectors["password_input"], password)
                            popup.click(self.selectors["password_next"])
                        except:
                            logger.info("Password field did not appear (possibly 2FA or passkey).")
            
            except Exception as e:
                logger.error(f"Error inside Google Popup: {e}")
                # Don't crash, user might be solving 2FA manually in the popup
            
            logger.info("Waiting for popup to close (User should complete login)...")
            try:
                # Wait for the popup to be closed (auth finished)
                # We give a long timeout here because 2FA might take time
                popup.wait_for_event("close", timeout=60000)
                logger.info("Popup closed. Returning to main window...")
            except:
                logger.warning("Popup did not close automatically. Checking main window status...")

            # --- BACK TO MAIN PAGE ---
            logger.info("Waiting for Claude Dashboard...")
            if self.wait_for_chat_input(timeout=30000):
                logger.info("Login successful.")
                return True
            else:
                raise AuthenticationError("Popup closed but Claude did not load.")

        except Exception as e:
            raise AuthenticationError(f"Google Login Flow failed: {e}")

    def is_fully_ready(self) -> bool:
        """Check if chat input is visible."""
        return self.page.is_visible(self.selectors["chat_input"])

    def wait_for_chat_input(self, timeout=30000) -> bool:
        """Waits for chat input, handling potential blocking dialogs."""
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout:
            self.handle_dialogs()
            if self.page.is_visible(self.selectors["chat_input"]):
                return True
            time.sleep(1)
        return False

    def handle_dialogs(self):
        try:
            # Common "Next" / "Done" / "Dismiss" modals in Claude
            for btn_text in ["Next", "Done", "Dismiss", "Get started"]:
                selector = f"div[role='dialog'] button:has-text('{btn_text}')"
                if self.page.is_visible(selector):
                    # Verify it's not a button we actually want (like 'Send')
                    self.page.click(selector)
        except:
            pass

    def send_prompt(self, prompt: str) -> str:
        if not self.is_fully_ready():
            logger.warning("Chat input not ready. Waiting...")
            if not self.wait_for_chat_input(timeout=10000):
                raise PromptError("Chat input missing. Cannot send prompt.")

        self.handle_dialogs()
        
        try:
            logger.info("Entering prompt...")
            input_loc = self.page.locator(self.selectors["chat_input"])
            input_loc.click()
            self.page.keyboard.type(prompt)
            
            logger.info("Clicking send...")
            send_btn = self.page.locator(self.selectors["send_btn"])
            expect(send_btn).not_to_be_disabled()
            send_btn.click()
            
        except Exception as e:
            raise PromptError(f"Failed to send prompt: {e}")

        logger.info("Waiting for response generation...")
        try:
            self.page.wait_for_selector(self.selectors["stop_btn"], timeout=10000)
            self.page.wait_for_selector(self.selectors["stop_btn"], state="hidden", timeout=120000)
        except PlaywrightTimeoutError:
            if not self.page.is_visible(f'{self.selectors["send_btn"]}:not([disabled])'):
                 raise PromptError("Timeout waiting for response generation.")

        try:
            logger.info("Extracting response...")
            copy_btns = self.page.locator(self.selectors["copy_btn"])
            self.page.wait_for_timeout(1000)
            
            if copy_btns.count() > 0:
                copy_btns.last.click()
                text = self.page.evaluate("async () => await navigator.clipboard.readText()")
                if text: return text.strip()
            
            msgs = self.page.locator(".font-claude-message")
            if msgs.count() > 0:
                return msgs.last.inner_text()
                
            return ""

        except Exception as e:
            raise PromptError(f"Failed to extract response: {e}")
