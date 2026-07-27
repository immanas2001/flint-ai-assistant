import os
from dotenv import load_dotenv

load_dotenv()

# ==========================
# AI Providers
# ==========================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Current provider
AI_PROVIDER = "gemini"

# Default Model
GEMINI_MODEL = "models/gemini-3.5-flash"