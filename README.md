# LLMSession

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/llm-session.svg)](https://pypi.org/project/llm-session/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A zero-configuration tool to automate interactions with web-based LLM providers (**ChatGPT** and **Claude**). It handles authentication, session persistence, and chained prompt execution programmatically.

## Features
- **Multi-Provider Support**: Automate interactions with all ChatGPT, AIStudio and Claude (Anthropic).
- **Zero-Config Setup**: Automatically handles browser binaries via Playwright.
- **Session Persistence**: Reuses cookies/storage for subsequent runs (no need to login every time).
- **Resilient**: Allows custom CSS selectors to adapt to UI changes without updating the library.

## Prerequisites
You must set the following environment variables, or pass them directly to the constructor via the `credentials` dictionary.(Currently, Use google account only in order to login)

**Google Login:**
- `LLM_EMAIL`
- `LLM_PASSWORD`

## Disclaimer
> [!WARNING]
> **Cloudflare/Bot Detection**: Automated interactions with web providers are subject to high-security bot detection. This library uses standard browser automation and may be blocked. For production reliability, please use the Official OpenAI or Anthropic APIs.

This tool automates a third-party web interface. It is subject to breakage if the target website changes its DOM structure. Use responsibly and in accordance with the provider's Terms of Service.

---

## Installation

```bash
pip install llm-session
```

---

## Quick Start

```python
import logging
from llm_session import Automator

# 1. Configure Standard Logging
logging.basicConfig(level=logging.INFO)

# 2. Define OTP Callback (Optional)
def my_otp_handler():
    return input("Enter OTP Code sent to email: ")

# 3. Initialize (Select 'chatgpt' or 'claude')
bot = Automator(
    provider="claude",  # Options: "chatgpt", "claude"
    headless=False,     # Set to True for headless mode (may increase detection risk)
    credentials={
        "email": "your_email@example.com", 
        "password": "your_password",
        "method": "google" # Claude provider defaults to Google Auth flows
    },
    on_otp_required=my_otp_handler
)

# 4. Single Prompt
print(bot.process_prompt("Hello, world!"))

# 5. Chained Prompt (Inject previous response)
chain = [
    "Write a haiku about Python.",
    "Translate this haiku to Spanish: {{previous}}"
]
responses = bot.process_chain(chain)
print(responses)

bot.close()
```

---

## Advanced Configuration

### Custom Selectors

Websites change their layout often. If a provider updates their CSS class names, you don't need to wait for a package update. You can inject your own selectors during initialization.

```python
bot = Automator(
    provider="chatgpt", 
    config={
        "selectors": {
            "textarea": "#new-prompt-id",
            "send_btn": ".new-send-button-class",
            "assistant_msg": ".new-message-wrapper"
        }
    }
)
```

### Using Environment Variables

Instead of passing credentials directly, you can use environment variables:

```python
import os

os.environ["LLM_EMAIL"] = "your_email@example.com"
# The library will detect these automatically

bot = Automator(provider="claude", headless=False)
```

---

## Session Management

This library stores browser cookies and local storage in your OS's standard user data directory. This allows the browser to maintain a "Logged In" state between script executions.

- **Windows**: `%LOCALAPPDATA%\LLMSession`
- **Linux**: `~/.local/share/LLMSession`
- **macOS**: `~/Library/Application Support/LLMSession`

**Key Features:**
- **Persistence**: Sessions persist across reboots.
- **Context Isolation**: Each session runs in a persistent browser context.
- **Security**: Sensitive data is stored locally and never transmitted.

---

## API Reference

### `Automator`

The main class for automating LLM interactions.

#### Constructor

```python
Automator(
    provider: str,
    headless: bool = False,
    credentials: dict = None,
    session_path: str = None,
    config: dict = None,
    on_otp_required: callable = None
)
```

**Parameters:**
- `provider` (str): The LLM provider to use. Supported: `"chatgpt"`, `"claude"`.
- `headless` (bool): Whether to run browser in headless mode. Default: `False`.
- `credentials` (dict): Dictionary containing login credentials:
  - `email` (str): Login email.
  - `password` (str): Login password.
  - `method` (str): "email" or "google".
- `session_path` (str, optional): Custom path for session storage. If not provided, uses OS default.
- `config` (dict, optional): Configuration options including custom selectors.
- `on_otp_required` (callable, optional): Callback function to handle OTP/2FA challenges.

#### Methods

##### `process_prompt(prompt: str) -> str`

Process a single prompt and return the response.

```python
response = bot.process_prompt("What is Python?")
print(response)
```

##### `process_chain(prompts: list) -> list`

Process a chain of prompts where `{{previous}}` in a prompt will be replaced with the previous response.

```python
chain = [
    "Write a poem about clouds.",
    "Translate the following to French: {{previous}}"
]
responses = bot.process_chain(chain)
```

##### `close()`

Close the browser and clean up resources.

```python
bot.close()
```

---

## Troubleshooting

### Issue: Login fails with "Invalid credentials"
**Solution**: 
- Verify your email and password.
- Check if you have 2FA enabled (provide `on_otp_required` callback).
- **Claude Users**: If using Google Auth, ensure the browser window (non-headless) allows you to click through any security prompts initially.

### Issue: "Cloudflare challenge detected"
**Solution**: 
- This library uses standard browser automation which may be detected.
- Try running with `headless=False` to solve CAPTCHA manually.

### Issue: Popup not closing (Claude/Google Auth)
**Solution**:
- The library attempts to handle Google's "Continue" interstitial screens. If it gets stuck, manual intervention in `headless=False` mode usually fixes the session for future headless runs.

### Issue: Session not persisting
**Solution**: 
- Ensure the session directory has write permissions.
- Check if antivirus is blocking file writes.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to:
- Set up your development environment
- Run tests and verification scripts
- Submit pull requests
- Report issues

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.