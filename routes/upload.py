from pathlib import Path
import shutil
import uuid

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Form,
)

from services.file_service import extract_file_content
from services.chunker import chunk_document
from services.vector_store import add_document_chunks

from database.database import (
    create_chat,
    rename_chat,
    save_document,
)


router = APIRouter()


# ============================================================
# UPLOAD DIRECTORY
# ============================================================

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# SUPPORTED FILE TYPES
#
# These match the formats currently handled by
# services.file_service.py.
# ============================================================

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".csv",
    ".xlsx",
    ".xls",
    ".txt",
}


# ============================================================
# DATASET EXTENSIONS
# ============================================================

DATASET_EXTENSIONS = {
    ".csv",
    ".xlsx",
    ".xls",
}


# ============================================================
# UPLOAD
#
# Supports both:
#
# POST /upload
# POST /upload/{chat_id}
#
# This keeps the frontend simple while remaining compatible
# with direct chat-specific uploads.
# ============================================================

@router.post("/upload")
@router.post("/upload/{chat_id}")
async def upload_file(
    file: UploadFile = File(...),
    chat_id: int | None = None,
):

    # ========================================================
    # VALIDATE FILENAME
    # ========================================================

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename provided."
        )


    original_filename = Path(
        file.filename
    ).name


    # ========================================================
    # GET EXTENSION
    # ========================================================

    extension = Path(
        original_filename
    ).suffix.lower()


    # ========================================================
    # VALIDATE EXTENSION
    # ========================================================

    if extension not in ALLOWED_EXTENSIONS:

        allowed = ", ".join(
            sorted(ALLOWED_EXTENSIONS)
        )

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type: {extension or 'unknown'}. "
                f"Supported types: {allowed}"
            )
        )


    # ========================================================
    # CREATE CHAT IF NECESSARY
    # ========================================================

    is_new_chat = False

    if chat_id is None:

        chat_id = create_chat()

        is_new_chat = True


    # ========================================================
    # GENERATE UNIQUE STORAGE NAME
    # ========================================================

    stored_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    filepath = (
        UPLOAD_DIR / stored_filename
    )


    # ========================================================
    # PROCESS FILE
    # ========================================================

    try:

        # ----------------------------------------------------
        # SAVE PHYSICAL FILE
        # ----------------------------------------------------

        with filepath.open(
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )


        print(
            "[Flint AI] File saved:",
            str(filepath)
        )


        # ----------------------------------------------------
        # EXTRACT CONTENT
        # ----------------------------------------------------

        extracted_text = extract_file_content(
            str(filepath)
        )


        extracted_text = (
            extracted_text or ""
        ).strip()


        if not extracted_text:

            raise ValueError(
                "No readable content was found "
                "in the uploaded file."
            )


        print(
            "[Flint AI] Extracted characters:",
            len(extracted_text)
        )


        # ----------------------------------------------------
        # SAVE DOCUMENT TO SQLITE
        # ----------------------------------------------------

        document_id = save_document(
            chat_id=chat_id,
            filename=original_filename,
            file_type=extension,
            content=extracted_text,
            file_path=str(filepath),
        )


        print(
            "[Flint AI] Document saved:",
            document_id
        )


        # ----------------------------------------------------
        # CHUNK DOCUMENT
        # ----------------------------------------------------

        chunks = chunk_document(
            extracted_text
        )


        if not chunks:

            raise ValueError(
                "The file was readable, but no "
                "document chunks could be created."
            )


        print(
            "[Flint AI] Created chunks:",
            len(chunks)
        )


        # ----------------------------------------------------
        # INDEX DOCUMENT
        # ----------------------------------------------------

        add_document_chunks(
            chat_id=chat_id,
            document_id=document_id,
            filename=original_filename,
            chunks=chunks,
        )


        print(
            "[Flint AI] Document indexed successfully."
        )


        # ====================================================
        # RENAME NEW CHAT
        # ====================================================

        if is_new_chat:

            title = (
                Path(original_filename).stem[:40]
                .strip()
            )

            if not title:
                title = "New Chat"

            rename_chat(
                chat_id,
                title
            )


        # ====================================================
        # RESPONSE
        # ====================================================

        response = {

            "success": True,

            "chat_id":
                chat_id,

            "document_id":
                document_id,

            "filename":
                original_filename,

            "file_type":
                extension,

            "characters":
                len(extracted_text),

            "chunks":
                len(chunks),

            "message":
                (
                    f"'{original_filename}' "
                    "uploaded and indexed successfully."
                ),

            "preview":
                extracted_text[:1000],

            "dataset": {

                "is_dataset":
                    extension in DATASET_EXTENSIONS,

                "file_path":
                    str(filepath)
                    if extension in DATASET_EXTENSIONS
                    else None,

                "file_type":
                    extension
                    if extension in DATASET_EXTENSIONS
                    else None,
            },
        }


        return response


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except HTTPException:
        raise


    except Exception as error:

        print(
            "[Flint AI] Upload Error:",
            repr(error)
        )


        # ----------------------------------------------------
        # REMOVE PARTIALLY PROCESSED FILE
        # ----------------------------------------------------

        if filepath.exists():

            try:
                filepath.unlink()

            except Exception as cleanup_error:

                print(
                    "[Flint AI] File cleanup failed:",
                    repr(cleanup_error)
                )


        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to process file: "
                f"{str(error)}"
            )
        )


    finally:

        await file.close()