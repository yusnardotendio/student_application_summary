import os
from dotenv import load_dotenv

load_dotenv()

ACTIVE_PROVIDER = os.getenv("ACTIVE_PROVIDER")

API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "google": os.getenv("GOOGLE_API_KEY"),
}
