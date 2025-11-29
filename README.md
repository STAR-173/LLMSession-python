# LLMSession

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build and Publish](https://github.com/star-173/llm_session/actions/workflows/publish.yml/badge.svg)](https://github.com/star-173/llm_session/actions/workflows/publish.yml)
[![PyPI version](https://badge.fury.io/py/llm-session.svg)](https://pypi.org/project/llm-session/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A zero-configuration tool to automate interactions with web-based LLM providers (currently ChatGPT). It handles authentication, session persistence, and chained prompt execution programmatically.

## Features
- **Zero-Config Setup**: Automatically handles browser binaries via Playwright.
- **Session Persistence**: Reuses cookies/storage for subsequent runs (no need to login every time).
- **Smart OTP Handling**: Supports non-blocking callbacks for 2FA/OTP challenges.
- **Resilient**: Allows custom CSS selectors to adapt to UI changes without updating the library.

## Prerequisites
You must set the following environment variables, or pass them directly to the constructor:
- `CHATGPT_EMAIL`
- `CHATGPT_PASSWORD`
- `CHATGPT_GOOGLE_LOGIN` (Optional: set to "true" if using Google Auth. *Note: Google Auth is experimental and may require manual intervention.*)

## Disclaimer
> [!WARNING]
> **Cloudflare/Bot Detection**: Automated interactions with ChatGPT are subject to high-security bot detection (Cloudflare). This library uses standard browser automation and may be blocked. For production reliability, please use the Official OpenAI API.

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

# 2. Define OTP Callback (Optional, but recommended for headless envs)
def my_otp_handler():
    # In production, you might fetch this from an email API
    return input("Enter OTP Code sent to email: ")

# 3. Initialize
bot = Automator(
    provider="chatgpt",
    headless=False,  # Set to True for production (CURRENTLY ONLY WORKS WITH headless=False)
    credentials={
        "email": "your_email@example.com", 
        "password": "your_password",
        "method": "email" # or "google"
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

Websites change their layout often. If ChatGPT updates their CSS class names, you don't need to wait for a package update. You can inject your own selectors during initialization.

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

os.environ["CHATGPT_EMAIL"] = "your_email@example.com"
os.environ["CHATGPT_PASSWORD"] = "your_password"

bot = Automator(provider="chatgpt", headless=False)
```

---

## Session Management

This library stores browser cookies and local storage in your OS's standard user data directory:
- **Windows**: `%LOCALAPPDATA%\LLMSession`
- **Linux**: `~/.local/share/LLMSession`
- **macOS**: `~/Library/Application Support/LLMSession`

**Key Features:**
- **Persistence**: Sessions persist across reboots—no need to login every time
- **Security**: Sensitive data is stored locally and never transmitted
- **Reusable**: Once authenticated, subsequent runs will skip the login process

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
- `provider` (str): The LLM provider to use (currently only "chatgpt" is supported)
- `headless` (bool): Whether to run browser in headless mode. Default: `False`
- `credentials` (dict): Dictionary containing login credentials:
  - `email` (str): Login email
  - `password` (str): Login password
  - `method` (str): Authentication method - "email" or "google". Default: "email"
- `session_path` (str, optional): Custom path for session storage. If not provided, uses OS default
- `config` (dict, optional): Configuration options including custom selectors
- `on_otp_required` (callable, optional): Callback function to handle OTP/2FA challenges

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

## Examples

### Example 1: Basic Usage

```python
from llm_session import Automator

bot = Automator(
    provider="chatgpt",
    headless=False,
    credentials={
        "email": "user@example.com",
        "password": "password123"
    }
)

response = bot.process_prompt("Explain quantum computing in simple terms.")
print(response)

bot.close()
```

### Example 2: Chained Prompts

```python
from llm_session import Automator

bot = Automator(provider="chatgpt", headless=False)

# Create a story step by step
chain = [
    "Write the first paragraph of a sci-fi story.",
    "Continue this story: {{previous}}",
    "Write a dramatic ending for: {{previous}}"
]

story_parts = bot.process_chain(chain)
full_story = "\n\n".join(story_parts)
print(full_story)

bot.close()
```

### Example 3: With OTP Handler

```python
from llm_session import Automator

def handle_otp():
    """Fetch OTP from email or user input"""
    code = input("Enter the OTP sent to your email: ")
    return code

bot = Automator(
    provider="chatgpt",
    headless=False,
    credentials={
        "email": "user@example.com",
        "password": "password123"
    },
    on_otp_required=handle_otp
)

response = bot.process_prompt("Hello!")
print(response)

bot.close()
```

---

## Troubleshooting

### Issue: Login fails with "Invalid credentials"
**Solution**: 
- Verify your email and password are correct
- Check if you have 2FA enabled (provide `on_otp_required` callback)
- Try logging in manually in a browser first to ensure your account is accessible

### Issue: "Cloudflare challenge detected"
**Solution**: 
- This library uses standard browser automation which may be detected
- Try running with `headless=False` to solve CAPTCHA manually
- For production use, consider using the official OpenAI API instead

### Issue: Selectors not working after ChatGPT update
**Solution**: 
- Use the custom selectors feature to update CSS selectors
- Or wait for a library update with fixed selectors
- Check GitHub issues for community-reported solutions

### Issue: Session not persisting
**Solution**: 
- Ensure the session directory has write permissions
- Check if antivirus is blocking file writes
- Try specifying a custom `session_path` with known write access

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

---

## Support

- **Issues**: [GitHub Issues](https://github.com/star-173/llm_session/issues)
- **Discussions**: [GitHub Discussions](https://github.com/star-173/llm_session/discussions)

