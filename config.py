import os

from dotenv import load_dotenv


load_dotenv()


# ============================================================
# AI PROVIDER
# ============================================================

AI_PROVIDER = os.getenv(
    "AI_PROVIDER",
    "gemini",
)


# ============================================================
# GEMINI
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY"
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "models/gemini-3.5-flash",
)


# ============================================================
# FUTURE PROVIDERS
# ============================================================

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)