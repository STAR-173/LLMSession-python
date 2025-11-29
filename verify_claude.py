import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.append(str(Path(__file__).parent / "python" / "src"))
sys.path.append(str(Path(__file__).parent / "src"))

from llm_session import Automator

import logging

logging.basicConfig(level=logging.INFO)

def main():
    print("--- Starting Claude Verification ---")

    # Use environment variables or hardcode for testing
    email = os.getenv("LLM_EMAIL", "your_email@gmail.com")
    password = os.getenv("LLM_PASSWORD", "your_password")

    try:
        print("Initializing Automator (claude)...")
        # RUN HEADLESS=FALSE FOR FIRST LOGIN
        bot = Automator(
            provider="claude",
            headless=False, 
            credentials={
                "email": email, 
                "password": password
            }
        )

        print("\n[Test] Single Prompt")
        prompt = "Explain quantum entanglement in 10 words."
        print(f"Sending: {prompt}")
        
        response = bot.process_prompt(prompt)
        print(f"\nResponse received:\n{response}")

        if len(response) > 5:
            print("\n>> Verification PASSED")
        else:
            print("\n>> Verification FAILED (Empty response)")
        
        time.sleep(2)
        bot.close()
        print("\n--- Verification Complete ---")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()