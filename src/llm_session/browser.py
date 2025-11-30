import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, BrowserContext, Page, Playwright
import appdirs

from .exceptions import SetupError

class BrowserManager:
    """Manages the Playwright browser instance and persistent context."""

    def __init__(self, app_name: str = "LLMSession"):
        self.default_user_data_dir = Path(appdirs.user_data_dir(app_name, appauthor=False))
        self.playwright: Optional[Playwright] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self, headless: bool = True, session_path: Optional[str] = None) -> Page:
        """
        Start the browser with a persistent context.
        
        Args:
            headless: Whether to run in headless mode.
            session_path: (Override) Path to the specific directory to store this session/profile.
        """
        if session_path:
            user_data_dir = Path(session_path)
        else:
            user_data_dir = self.default_user_data_dir

        if not user_data_dir.exists():
            user_data_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.playwright = sync_playwright().start()
        except Exception as e:
             raise SetupError(f"Failed to start Playwright. Make sure it is installed: {e}")
        
        # Launch persistent context
        try:
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-infobars",
                    "--exclude-switches=enable-automation",
                    "--disable-background-timer-throttling",
                    "--disable-backgrounding-occluded-windows",
                    "--disable-renderer-backgrounding"
                ]
            )
        except Exception as e:
            raise SetupError(f"Failed to launch browser: {e}")
        
        if len(self.context.pages) > 0:
            self.page = self.context.pages[0]
        else:
            self.page = self.context.new_page()
            
        return self.page

    def stop(self):
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()

    def is_authenticated(self, check_url: str, check_selector: str) -> bool:
        if not self.page:
            raise SetupError("Browser not started.")
        try:
            self.page.goto(check_url, wait_until="domcontentloaded")
            try:
                self.page.wait_for_selector(check_selector, timeout=5000)
                return True
            except:
                return False
        except Exception as e:
            return False
    
    def save_session(self, path: str):
        if self.context:
            try:
                self.context.storage_state(path=path)
            except:
                pass