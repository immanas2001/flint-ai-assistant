from google import genai
from config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)

MODELS = [
    "models/gemini-3.5-flash",
    "models/gemini-2.0-flash",
    "models/gemini-flash-latest",
]


def generate_response(prompt: str):

    last_error = None

    for model in MODELS:

        try:

            response = client.models.generate_content(
                model=model,
                contents=prompt,
            )

            return response.text

        except Exception as e:

            last_error = e
            continue

    return f"❌ Gemini Error:\n{last_error}"