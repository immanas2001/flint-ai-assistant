"""
Conversation memory for Flint AI.
Currently stores messages in RAM.
Later this will be upgraded to SQLite.
"""

conversation_history = []


def add_message(role: str, message: str):
    """
    Add a message to the conversation history.
    """

    conversation_history.append(
        {
            "role": role,
            "message": message
        }
    )


def get_history():
    """
    Returns the conversation history.
    """

    return conversation_history


def clear_history():
    """
    Clears the conversation history.
    """

    conversation_history.clear()