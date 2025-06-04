import os
from dotenv import load_dotenv

load_dotenv()

ACTIVE_PROVIDER = os.getenv("ACTIVE_PROVIDER")

API_KEYS = {
    "openai_api_key": os.getenv("OPENAI_API_KEY"),
    "gemini_api_key": os.getenv("GEMINI_API_KEY"),
    "image_parsing_api_key": os.getenv("IMAGE_PARSING_API_KEY"),
}

MODEL_TO_USE = os.getenv("MODEL_TO_USE")
