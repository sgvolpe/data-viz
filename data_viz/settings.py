import logging
import os
from dotenv import load_dotenv

def load_settings():
    # Load .env file
    load_dotenv()  # automatically loads from project root .env
    #
    # # Access variables
    groq_api_key = os.getenv("GROQ_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    debug_mode = os.getenv("DEBUG", "False") == "True"

    print("Configuration Loaded Correctly.")


if __name__ == "__main__":
    load_settings()