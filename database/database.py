import sqlite3
from pathlib import Path


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE_DIR = Path("database")
DATABASE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

DB_PATH = DATABASE_DIR / "chat.db"


# ============================================================
# CONNECTION
# ============================================================

def get_connection() -> sqlite3.Connection:
    """
    Create and configure a SQLite database connection.
    """

    conn = sqlite3.connect(
        str(DB_PATH)
    )

    conn.row_factory = sqlite3.Row

    # Enable foreign-key constraints.
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def create_tables() -> None:
    """
    Create all required database tables.

    Existing tables are preserved.
    A small migration ensures older databases receive
    the documents.file_path column.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ----------------------------------------------------
        # Chats
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT DEFAULT 'New Chat',
                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
        """)


        # ----------------------------------------------------
        # Messages
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(chat_id)
                    REFERENCES chats(id)
                    ON DELETE CASCADE
            )
        """)


        # ----------------------------------------------------
        # Documents
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                content TEXT NOT NULL,
                file_path TEXT,
                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(chat_id)
                    REFERENCES chats(id)
                    ON DELETE CASCADE
            )
        """)


        # ----------------------------------------------------
        # Migration
        # ----------------------------------------------------

        cursor.execute(
            "PRAGMA table_info(documents)"
        )

        columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "file_path" not in columns:

            cursor.execute("""
                ALTER TABLE documents
                ADD COLUMN file_path TEXT
            """)


        # ----------------------------------------------------
        # Indexes
        # ----------------------------------------------------

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_messages_chat_id
            ON messages(chat_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_documents_chat_id
            ON documents(chat_id)
        """)


        conn.commit()

    finally:

        conn.close()


# ============================================================
# CHAT FUNCTIONS
# ============================================================

def create_chat(
    title: str = "New Chat"
) -> int:
    """
    Create a new chat and return its ID.
    """

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            INSERT INTO chats(title)
            VALUES(?)
            """,
            (title,)
        )

        chat_id = cursor.lastrowid

        conn.commit()

        return int(chat_id)

    finally:

        conn.close()


def get_all_chats() -> list[dict]:
    """
    Return all chats, newest first.
    """

    conn = get_connection()

    try:

        rows = conn.execute("""
            SELECT *
            FROM chats
            ORDER BY id DESC
        """).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


def rename_chat(
    chat_id: int,
    title: str
) -> None:
    """
    Rename an existing chat.
    """

    conn = get_connection()

    try:

        conn.execute(
            """
            UPDATE chats
            SET title=?
            WHERE id=?
            """,
            (
                title,
                chat_id
            )
        )

        conn.commit()

    finally:

        conn.close()


def delete_chat(
    chat_id: int
) -> None:
    """
    Delete a chat.

    Related messages and documents are automatically
    deleted because of ON DELETE CASCADE.
    """

    conn = get_connection()

    try:

        conn.execute(
            """
            DELETE FROM chats
            WHERE id=?
            """,
            (chat_id,)
        )

        conn.commit()

    finally:

        conn.close()


# ============================================================
# MESSAGE FUNCTIONS
# ============================================================

def save_message(
    chat_id: int,
    role: str,
    content: str
) -> None:
    """
    Save a message to a chat.
    """

    conn = get_connection()

    try:

        conn.execute(
            """
            INSERT INTO messages(
                chat_id,
                role,
                content
            )
            VALUES(?,?,?)
            """,
            (
                chat_id,
                role,
                content
            )
        )

        conn.commit()

    finally:

        conn.close()


def get_messages(
    chat_id: int
) -> list[dict]:
    """
    Return all messages for a chat in chronological order.
    """

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT *
            FROM messages
            WHERE chat_id=?
            ORDER BY id ASC
            """,
            (chat_id,)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


# ============================================================
# DOCUMENT FUNCTIONS
# ============================================================

def save_document(
    chat_id: int,
    filename: str,
    file_type: str,
    content: str,
    file_path: str | None = None
) -> int:
    """
    Save an uploaded document and return its database ID.
    """

    conn = get_connection()

    try:

        cursor = conn.execute(
            """
            INSERT INTO documents(
                chat_id,
                filename,
                file_type,
                content,
                file_path
            )
            VALUES(?,?,?,?,?)
            """,
            (
                chat_id,
                filename,
                file_type,
                content,
                file_path
            )
        )

        document_id = cursor.lastrowid

        conn.commit()

        return int(document_id)

    finally:

        conn.close()


def get_documents(
    chat_id: int
) -> list[dict]:
    """
    Return all documents belonging to a chat.
    """

    conn = get_connection()

    try:

        rows = conn.execute(
            """
            SELECT *
            FROM documents
            WHERE chat_id=?
            ORDER BY id ASC
            """,
            (chat_id,)
        ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    finally:

        conn.close()


def get_document(
    document_id: int
) -> dict | None:
    """
    Return a single document by ID.
    """

    conn = get_connection()

    try:

        row = conn.execute(
            """
            SELECT *
            FROM documents
            WHERE id=?
            """,
            (document_id,)
        ).fetchone()

        if row is None:
            return None

        return dict(row)

    finally:

        conn.close()


def delete_documents(
    chat_id: int
) -> None:
    """
    Delete all documents belonging to a chat.
    """

    conn = get_connection()

    try:

        conn.execute(
            """
            DELETE FROM documents
            WHERE chat_id=?
            """,
            (chat_id,)
        )

        conn.commit()

    finally:

        conn.close()