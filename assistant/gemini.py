from google import genai

from config import GEMINI_API_KEY, GEMINI_MODEL


# ==========================================
# Gemini Client
# ==========================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ==========================================
# Normal Response
# ==========================================

def generate_response(prompt: str) -> str:
    """
    Generate a complete Gemini response.

    Used by the existing /chat endpoint.
    """

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        return response.text or ""

    except Exception as e:
        return f"Gemini Error: {str(e)}"


# ==========================================
# Streaming Response
# ==========================================

def generate_stream(prompt: str):
    """
    Stream Gemini response chunks.

    Each yielded value is a piece of the
    final AI response.
    """

    try:

        response_stream = client.models.generate_content_stream(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        for chunk in response_stream:

            if hasattr(chunk, "text") and chunk.text:
                yield chunk.text

    except Exception as e:

        yield f"\n\nGemini Error: {str(e)}"