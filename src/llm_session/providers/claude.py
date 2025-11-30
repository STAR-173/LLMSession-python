import time
import logging
from typing import Optional, Callable
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect
from .base import LLMProvider
from ..exceptions import AuthenticationError, PromptError

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
        
        # Updated "Continue" selector to be more robust
        "google_continue_btn": 'button:has-text("Continue")', 
        
        # Chat Interface
        "chat_input": 'div[contenteditable="true"][data-testid="chat-input"]',
        "send_btn": 'button[aria-label="Send message"]',
        "stop_btn": 'button[aria-label="Stop response"]', 
        "copy_btn": 'button[data-testid="action-bar-copy"]',
        
        # --- Cookie Banner ---
        "cookie_banner": '[data-testid="consent-banner"]',
        "cookie_reject_btn": 'button[data-testid="consent-reject"]'
    }

    def __init__(self, page: Page, config: Optional[dict] = None, on_otp_required: Optional[Callable[[], str]] = None):
        super().__init__(page)
        self.config = config or {}
        self.on_otp_required = on_otp_required
        self.selectors = self.DEFAULT_SELECTORS.copy()
        
        if "selectors" in self.config:
            self.selectors.update(self.config["selectors"])
            
        self.SEL_PROFILE_BTN = self.selectors["chat_input"]

    def login(self, credentials: dict) -> bool:
        logger.info("Starting Claude login process...")
        email = credentials.get("email")
        password = credentials.get("password")

        # 1. Navigation
        try:
            self.page.goto(self.URL, wait_until="commit")
        except:
            pass 
        
        # Check cookies immediately on load
        self.handle_dialogs()

        # 2. Race Condition Check
        login_sel = self.selectors["login_google_btn"]
        chat_sel = self.selectors["chat_input"]
        
        logger.info("Waiting for interface to hydrate...")
        try:
            self.page.wait_for_selector(f"{login_sel}, {chat_sel}", state="visible", timeout=15000)
        except PlaywrightTimeoutError:
            if self.page.is_visible(self.selectors["user_menu_btn"]):
                self.page.reload()
                self.page.wait_for_selector(chat_sel, timeout=10000)
            else:
                raise AuthenticationError("Timeout waiting for Login Button or Chat Input.")

        if self.page.is_visible(chat_sel):
            logger.info("Already logged in.")
            return True
        elif self.page.is_visible(login_sel):
            return self._perform_google_login(email, password)
        else:
            raise AuthenticationError("Interface loaded but recognized elements are missing.")

    def _perform_google_login(self, email, password):
        """Handles the Google Login Popup Flow."""
        logger.info("Login button found. Initiating Google Auth...")
        
        try:
            with self.page.expect_popup() as popup_info:
                self.page.click(self.selectors["login_google_btn"], force=True)
            
            popup = popup_info.value
            
            # 3. Popup Interaction
            account_selector = f'div[role="link"][data-identifier="{email}"]'
            email_input_sel = self.selectors["email_input"]
            
            try:
                popup.wait_for_selector(f'{email_input_sel}, {account_selector}', timeout=10000)
            except:
                popup.wait_for_load_state("domcontentloaded")
            
            # Path A: Account Tile
            if popup.locator(account_selector).is_visible():
                logger.info(f"Clicking account tile for {email}...")
                popup.click(account_selector, force=True)
            
            # Path B: Email & Password
            else:
                logger.info("Entering Email...")
                popup.fill(self.selectors["email_input"], email)
                popup.click(self.selectors["email_next"])
                
                if password:
                    popup.wait_for_selector(self.selectors["password_input"], state="visible", timeout=5000)
                    popup.fill(self.selectors["password_input"], password)
                    try:
                        popup.click(self.selectors["password_next"])
                    except Exception as e:
                        logger.warning(f"Error clicking password next: {e}")

            # Unified 'Continue' Button
            try:
                continue_btn_sel = self.selectors["google_continue_btn"]
                if not popup.is_closed():
                    popup.wait_for_selector(continue_btn_sel, state="visible", timeout=10000)
                    logger.info("Found Google 'Continue' button. Clicking...")
                    popup.click(continue_btn_sel, force=True)
                    popup.wait_for_timeout(1000)
                    if popup.is_visible(continue_btn_sel) and not popup.is_closed():
                        popup.click(continue_btn_sel, force=True)
            except PlaywrightTimeoutError:
                pass
            except Exception as e:
                logger.debug(f"Continue button logic bypassed: {e}")

            # Finalize
            try:
                popup.wait_for_event("close", timeout=60000)
            except:
                logger.warning("Popup did not close automatically. Checking main window...")

            if self.wait_for_chat_input(timeout=30000):
                logger.info("Login successful.")
                return True
            else:
                raise AuthenticationError("Popup closed but Claude did not load.")

        except Exception as e:
            raise AuthenticationError(f"Google Login Flow failed: {e}")

    def is_fully_ready(self) -> bool:
        return self.page.is_visible(self.selectors["chat_input"])

    def wait_for_chat_input(self, timeout=30000) -> bool:
        try:
            self.page.wait_for_selector(self.selectors["chat_input"], state="visible", timeout=timeout)
            self.handle_dialogs()
            return True
        except:
            return False

    def handle_dialogs(self):
        """Handle Cookie Banners and standard dialogs."""
        # 1. Cookie Banner
        try:
            if self.page.is_visible(self.selectors["cookie_banner"]):
                logger.info("Cookie banner detected. Rejecting...")
                self.page.click(self.selectors["cookie_reject_btn"])
                # Wait briefly for it to disappear
                self.page.wait_for_selector(self.selectors["cookie_banner"], state="hidden", timeout=3000)
        except Exception as e:
            # We don't want to crash if the banner check fails or doesn't exist
            logger.debug(f"Cookie banner check ignored: {e}")

        # 2. General Dialogs (Escape)
        try:
            if self.page.is_visible("div[role='dialog']"):
                self.page.keyboard.press("Escape")
        except:
            pass

    def send_prompt(self, prompt: str) -> str:
        if not self.is_fully_ready():
            self.wait_for_chat_input(timeout=10000)

        # Ensure no banners block the view
        self.handle_dialogs()
        
        try:
            self.page.click(self.selectors["chat_input"])
            self.page.keyboard.type(prompt)
            self.page.wait_for_timeout(300) 
            self.page.click(self.selectors["send_btn"])
        except Exception as e:
            raise PromptError(f"Failed to send prompt: {e}")

        try:
            self.page.wait_for_selector(self.selectors["stop_btn"], timeout=10000)
            self.page.wait_for_selector(self.selectors["stop_btn"], state="hidden", timeout=120000)
        except PlaywrightTimeoutError:
            pass 

        try:
            copy_btns = self.page.locator(self.selectors["copy_btn"])
            if copy_btns.count() > 0:
                copy_btns.last.click()
                return self.page.evaluate("async () => await navigator.clipboard.readText()").strip()
            
            msgs = self.page.locator(".font-claude-message")
            if msgs.count() > 0:
                return msgs.last.inner_text()
            return ""
        except Exception as e:
            raise PromptError(f"Extraction failed: {e}")