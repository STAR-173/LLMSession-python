import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add src to path so we can import without installing
sys.path.append(str(Path(__file__).parent / "python" / "src"))
# Fallback if running from inside python folder
sys.path.append(str(Path(__file__).parent / "src"))

from llm_session import Automator

import logging

# 1. Configure Standard Logging
logging.basicConfig(level=logging.INFO)

def main():
    print("--- Starting AI Studio Verification ---")

    # CREDENTIALS: Set these or ensure they are in your Environment Variables
    # You can also hardcode them here for a quick test, but don't commit them!
    email = os.getenv("LLM_EMAIL", "your_email@gmail.com")
    password = os.getenv("LLM_PASSWORD", "your_password")

    if email == "your_email@gmail.com":
        print("WARNING: Using default/dummy credentials. Login will likely fail.")
        print("Please set LLM_EMAIL and LLM_PASSWORD environment variables or edit the script.")

    try:
        # Initialize Automator with 'aistudio' provider
        # headless=False is CRITICAL for the first run to handle Google Login manually
        print("Initializing Automator (aistudio)...")
        bot = Automator(
            provider="aistudio",
            headless=False, 
            credentials={
                "email": email, 
                "password": password
            }
        )

        # Test 1: Single Prompt
        print("\n[Test 1] Single Prompt")
        prompt = "Explain the concept of recursion in one sentence."
        print(f"Sending: {prompt}")
        
        response = bot.process_prompt(prompt)
        print(f"\nResponse received:\n{response}")

        # Test 2: Chained Context
        # We verify that the session remembers context
        print("\n[Test 2] Follow-up Prompt (Context Check)")
        follow_up = "Give me a Python code example of it."
        print(f"Sending: {follow_up}")
        
        response_2 = bot.process_chain([follow_up])
        print(f"\nResponse received:\n{response_2[0]}")

        print("\n>> Verification PASSED if you see meaningful responses above.")
        
        # Keep browser open for a moment to see the result
        time.sleep(2)
        bot.close()
        print("\n--- Verification Complete ---")

    except Exception as e:
        print(f"\nERROR during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()