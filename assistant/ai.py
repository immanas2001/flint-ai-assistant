from assistant.prompts import SYSTEM_PROMPT
from assistant.gemini import generate_response, generate_stream

from database.database import get_documents
from services.vector_store import search_documents


# ==========================================
# RAG Configuration
# ==========================================

TOP_K_RESULTS = 5


# ==========================================
# Retrieve Relevant Context
# ==========================================

def retrieve_context(
    query: str,
    chat_id: int,
    n_results: int = TOP_K_RESULTS
):
    """
    Retrieve relevant chunks from ChromaDB.

    Returns:

    {
        "context": "...",
        "sources": [...]
    }
    """

    documents = get_documents(chat_id)

    if not documents:

        return {
            "context": "",
            "sources": []
        }

    if not query.strip():

        return {
            "context": "",
            "sources": []
        }

    try:

        results = search_documents(
            chat_id=chat_id,
            query=query,
            n_results=n_results
        )

    except Exception as e:

        print(
            "RAG Search Error:",
            repr(e)
        )

        return {
            "context": "",
            "sources": []
        }


    retrieved_documents = (
        results.get("documents", [[]])
    )

    retrieved_metadata = (
        results.get("metadatas", [[]])
    )


    if not retrieved_documents:

        return {
            "context": "",
            "sources": []
        }


    chunks = retrieved_documents[0]

    metadata_list = (
        retrieved_metadata[0]
        if retrieved_metadata
        else []
    )


    if not chunks:

        return {
            "context": "",
            "sources": []
        }


    context_parts = []
    sources = []


    # ==========================================
    # Build Retrieved Context
    # ==========================================

    for index, chunk in enumerate(chunks):

        metadata = {}

        if index < len(metadata_list):
            metadata = (
                metadata_list[index]
                or {}
            )


        filename = metadata.get(
            "filename",
            "Unknown document"
        )

        document_id = metadata.get(
            "document_id",
            ""
        )

        chunk_index = metadata.get(
            "chunk_index",
            index
        )


        context_parts.append(
            f"""
--- Retrieved Document Chunk {index + 1} ---

Source: {filename}
Chunk: {chunk_index}

{chunk}

--- End Chunk {index + 1} ---
"""
        )


        # ==========================================
        # Source Metadata
        # ==========================================

        sources.append({
            "filename": filename,
            "document_id": document_id,
            "chunk_index": chunk_index
        })


    return {
        "context": "\n".join(
            context_parts
        ),
        "sources": sources
    }


# ==========================================
# Build Prompt
# ==========================================

def build_prompt(
    messages: list,
    chat_id: int
):

    conversation = (
        SYSTEM_PROMPT +
        "\n\n"
    )


    # ==========================================
    # Latest User Question
    # ==========================================

    latest_question = ""

    for msg in reversed(messages):

        if msg.get("role") == "user":

            latest_question = (
                msg.get("content", "")
            )

            break


    # ==========================================
    # Retrieve RAG Context
    # ==========================================

    rag = retrieve_context(
        query=latest_question,
        chat_id=chat_id,
        n_results=TOP_K_RESULTS
    )


    retrieved_context = rag["context"]


    if retrieved_context:

        conversation += """
========== RELEVANT DOCUMENT CONTEXT ==========

Use the retrieved document context when
answering questions about uploaded files.

Rules:

- Prefer the retrieved document information.
- Do not invent information that is not
  supported by the retrieved context.
- If the context is insufficient, say so.
- Do not claim information exists in a
  document when it was not retrieved.

"""

        conversation += retrieved_context

        conversation += """

========== END DOCUMENT CONTEXT ==========

"""


    # ==========================================
    # Chat History
    # ==========================================

    conversation += (
        "========== CHAT HISTORY ==========\n\n"
    )


    for msg in messages:

        role = msg.get(
            "role",
            "user"
        )

        if role == "assistant":

            role_name = "Flint AI"

        else:

            role_name = "User"


        content = msg.get(
            "content",
            ""
        )


        conversation += (
            f"{role_name}: {content}\n"
        )


    conversation += "\nFlint AI:"

    return conversation


# ==========================================
# Normal Response
# ==========================================

def ask_ai(
    messages: list,
    chat_id: int
):

    prompt = build_prompt(
        messages,
        chat_id
    )

    return generate_response(
        prompt
    )


# ==========================================
# Streaming Response
# ==========================================

def ask_ai_stream(
    messages: list,
    chat_id: int
):

    prompt = build_prompt(
        messages,
        chat_id
    )

    return generate_stream(
        prompt
    )