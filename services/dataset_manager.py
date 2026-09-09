from pathlib import Path

from database.database import (
    get_documents
)


# ==========================================
# Upload Directory
# ==========================================

UPLOAD_DIR = Path("uploads")


# ==========================================
# Dataset Extensions
# ==========================================

DATASET_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}


# ==========================================
# Find Dataset For Chat
# ==========================================

def get_chat_dataset(
    chat_id: int
):
    """
    Find the latest CSV/Excel dataset
    belonging to the specified chat.

    Uses the exact file_path stored in SQLite.
    """

    documents = get_documents(
        chat_id
    )


    # ==========================================
    # Find Dataset Documents
    # ==========================================

    dataset_documents = [

        document

        for document in documents

        if str(
            document.get(
                "file_type",
                ""
            )
        ).lower()
        in DATASET_EXTENSIONS

    ]


    if not dataset_documents:

        print(
            f"[Dataset Manager] "
            f"No dataset found for chat {chat_id}"
        )

        return None


    # ==========================================
    # Latest Dataset
    # ==========================================

    document = dataset_documents[-1]


    filename = document[
        "filename"
    ]


    extension = Path(
        filename
    ).suffix.lower()


    # ==========================================
    # Use Stored Exact File Path
    # ==========================================

    stored_path = document.get(
        "file_path"
    )


    if stored_path:

        filepath = Path(
            stored_path
        )


        # --------------------------------------
        # Verify File Exists
        # --------------------------------------

        if filepath.exists():

            print(
                "[Dataset Manager] "
                "Using stored dataset:"
            )

            print(
                f"  Chat ID: {chat_id}"
            )

            print(
                f"  Filename: {filename}"
            )

            print(
                f"  Path: {filepath}"
            )


            return {

                "filepath":
                    str(filepath),

                "filename":
                    filename,

                "file_type":
                    extension,

                "document_id":
                    document["id"],

            }


        # ======================================
        # Stored Path Doesn't Exist
        # ======================================

        print(
            "[Dataset Manager] "
            "Stored file does not exist:"
        )

        print(
            f"  {filepath}"
        )


    # ==========================================
    # Backward Compatibility
    #
    # This handles datasets uploaded before
    # file_path was added to the database.
    # ==========================================

    matching_files = list(
        UPLOAD_DIR.glob(
            f"*{extension}"
        )
    )


    if not matching_files:

        print(
            "[Dataset Manager] "
            "No physical dataset found."
        )

        return None


    # ==========================================
    # Latest Physical File
    # ==========================================

    filepath = max(
        matching_files,
        key=lambda file:
            file.stat().st_mtime
    )


    print(
        "[Dataset Manager] "
        "Using fallback dataset:"
    )

    print(
        f"  Chat ID: {chat_id}"
    )

    print(
        f"  Filename: {filename}"
    )

    print(
        f"  Path: {filepath}"
    )


    return {

        "filepath":
            str(filepath),

        "filename":
            filename,

        "file_type":
            extension,

        "document_id":
            document["id"],

    }