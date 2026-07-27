from assistant.prompts import SYSTEM_PROMPT
from assistant.gemini import generate_response
from assistant.memory import (
    add_message,
    get_history,
)


def ask_ai(user_message: str) -> str:

    add_message("user", user_message)

    history = get_history()

    conversation = SYSTEM_PROMPT + "\n\n"

    for msg in history:
        conversation += f"{msg['role'].title()}: {msg['message']}\n"

    conversation += "\nFlint AI:"

    response = generate_response(conversation)

    add_message("assistant", response)

    return response