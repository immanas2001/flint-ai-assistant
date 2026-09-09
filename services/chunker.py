from typing import List


# ==========================================
# Chunk Configuration
# ==========================================

DEFAULT_CHUNK_SIZE = 1500
DEFAULT_OVERLAP = 200


# ==========================================
# Clean Text
# ==========================================

def clean_text(text: str) -> str:
    """
    Clean extracted document text before chunking.
    """

    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    lines = []

    for line in text.split("\n"):

        line = " ".join(line.split())

        if line:
            lines.append(line)

    return "\n".join(lines)


# ==========================================
# Chunk Text
# ==========================================

def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP
) -> List[str]:
    """
    Split a document into overlapping chunks.

    Example:

        chunk 1: characters 0 - 1500
        chunk 2: characters 1300 - 2800
        chunk 3: characters 2600 - 4100

    The overlap helps preserve context between chunks.
    """

    text = clean_text(text)

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative"
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:

        end = min(
            start + chunk_size,
            text_length
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - overlap

    return chunks


# ==========================================
# Document Chunking
# ==========================================

def chunk_document(
    content: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP
) -> List[dict]:
    """
    Convert document content into structured chunks.

    Returns:

    [
        {
            "chunk_index": 0,
            "content": "..."
        },
        ...
    ]
    """

    chunks = chunk_text(
        content,
        chunk_size=chunk_size,
        overlap=overlap
    )

    return [
        {
            "chunk_index": index,
            "content": chunk
        }
        for index, chunk in enumerate(chunks)
    ]