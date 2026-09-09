import chromadb
from pathlib import Path


# ==========================================
# Configuration
# ==========================================

VECTOR_DB_DIR = Path("database/vector_db")

VECTOR_DB_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================
# ChromaDB Client
# ==========================================

client = chromadb.PersistentClient(
    path=str(VECTOR_DB_DIR)
)


# ==========================================
# Collection
# ==========================================

collection = client.get_or_create_collection(
    name="flint_documents",
    metadata={
        "description": "Flint AI document embeddings"
    }
)


# ==========================================
# Add Document Chunks
# ==========================================

def add_document_chunks(
    chat_id: int,
    document_id: int,
    filename: str,
    chunks: list[dict]
):
    """
    Store document chunks in ChromaDB.
    """

    if not chunks:
        return

    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:

        chunk_index = chunk["chunk_index"]
        content = chunk["content"]

        chunk_id = (
            f"chat_{chat_id}"
            f"_doc_{document_id}"
            f"_chunk_{chunk_index}"
        )

        ids.append(chunk_id)

        documents.append(content)

        metadatas.append({
            "chat_id": str(chat_id),
            "document_id": str(document_id),
            "filename": filename,
            "chunk_index": chunk_index
        })

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )


# ==========================================
# Search Documents
# ==========================================

def search_documents(
    chat_id: int,
    query: str,
    n_results: int = 5
):
    """
    Search uploaded documents and return
    both content and source metadata.
    """

    if not query.strip():
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

    try:

        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={
                "chat_id": str(chat_id)
            }
        )

        return results

    except Exception as e:

        print(
            "Vector search error:",
            repr(e)
        )

        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }


# ==========================================
# Delete Document
# ==========================================

def delete_document(
    chat_id: int,
    document_id: int
):
    """
    Delete all chunks belonging to one document.
    """

    collection.delete(
        where={
            "$and": [
                {
                    "chat_id": str(chat_id)
                },
                {
                    "document_id": str(document_id)
                }
            ]
        }
    )


# ==========================================
# Delete Chat Documents
# ==========================================

def delete_chat_documents(
    chat_id: int
):
    """
    Delete all vector chunks belonging
    to a chat.
    """

    collection.delete(
        where={
            "chat_id": str(chat_id)
        }
    )


# ==========================================
# Collection Count
# ==========================================

def get_collection_count() -> int:

    return collection.count()