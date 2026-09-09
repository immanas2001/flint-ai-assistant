# Flint AI

Flint AI is a modern AI assistant built with FastAPI, Google Gemini, SQLite, and ChromaDB.

It combines conversational AI with document understanding, dataset analysis, interactive charts, chat history, and retrieval-based document context.

---

## ✨ Features

### 🤖 AI Chat
- Google Gemini-powered conversations
- Streaming responses using Server-Sent Events
- Conversation history
- Follow-up questions
- Automatic chat creation
- Chat renaming
- Chat deletion

### 📄 Document Understanding
Flint AI currently supports:

- PDF
- TXT
- CSV
- XLSX
- XLS

Uploaded documents are extracted, chunked, stored, and made available to the AI retrieval pipeline.

### 🔎 RAG Foundation
Flint AI includes a ChromaDB-based vector store for document retrieval.

The current pipeline is:

```text
Upload Document
      ↓
Extract Content
      ↓
Chunk Document
      ↓
Store Chunks
      ↓
Vector Retrieval
      ↓
Relevant Context
      ↓
Gemini
      ↓
Answer