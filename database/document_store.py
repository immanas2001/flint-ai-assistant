from typing import Optional

# Temporary in-memory storage.
# Later we'll move this to SQLite.

_current_document = ""


def save_document(text: str) -> None:
    global _current_document
    _current_document = text


def get_document() -> str:
    return _current_document


def clear_document() -> None:
    global _current_document
    _current_document = ""