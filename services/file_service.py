from pathlib import Path

import pandas as pd
from PyPDF2 import PdfReader


# ============================================================
# CSV
# ============================================================

def extract_csv(filepath: str) -> str:
    """
    Extract useful textual information from a CSV dataset.

    Includes:
    - row/column counts
    - column names
    - data types
    - missing-value counts
    - first 20 rows
    - numeric statistics
    """

    try:
        df = pd.read_csv(filepath)

    except UnicodeDecodeError:
        try:
            df = pd.read_csv(
                filepath,
                encoding="latin-1"
            )

        except Exception as error:
            raise ValueError(
                f"Could not read CSV file: {error}"
            ) from error

    except Exception as error:
        raise ValueError(
            f"Could not read CSV file: {error}"
        ) from error


    if df.empty:
        return "The CSV file is empty."


    output = [
        "========== CSV DATASET ==========",
        "",
        f"Rows: {len(df)}",
        f"Columns: {len(df.columns)}",
        "",
        "========== COLUMNS ==========",
        "",
    ]


    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    for column in df.columns:
        output.append(
            f"- {column}"
        )


    # --------------------------------------------------------
    # Data Types
    # --------------------------------------------------------

    output.extend([
        "",
        "========== DATA TYPES ==========",
        "",
    ])


    for column, dtype in df.dtypes.items():
        output.append(
            f"{column}: {dtype}"
        )


    # --------------------------------------------------------
    # Missing Values
    # --------------------------------------------------------

    output.extend([
        "",
        "========== MISSING VALUES ==========",
        "",
    ])


    missing = df.isna().sum()

    has_missing = False


    for column, count in missing.items():

        if count > 0:

            has_missing = True

            output.append(
                f"{column}: {count}"
            )


    if not has_missing:
        output.append(
            "No missing values."
        )


    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    output.extend([
        "",
        "========== DATA PREVIEW ==========",
        "",
    ])


    output.append(
        df.head(20).to_string(
            index=False
        )
    )


    # --------------------------------------------------------
    # Numeric Summary
    # --------------------------------------------------------

    numeric_columns = (
        df.select_dtypes(
            include="number"
        ).columns
    )


    if len(numeric_columns) > 0:

        output.extend([
            "",
            "========== NUMERIC SUMMARY ==========",
            "",
        ])


        output.append(
            df[numeric_columns]
            .describe()
            .to_string()
        )


    return "\n".join(output)


# ============================================================
# EXCEL
# ============================================================

def extract_excel(filepath: str) -> str:
    """
    Extract information from every worksheet in an Excel file.
    """

    try:

        sheets = pd.read_excel(
            filepath,
            sheet_name=None
        )

    except Exception as error:

        raise ValueError(
            f"Could not read Excel file: {error}"
        ) from error


    if not sheets:
        return "The Excel file contains no worksheets."


    output = [
        "========== EXCEL DOCUMENT ==========",
        "",
    ]


    for sheet_name, df in sheets.items():

        output.extend([
            "",
            f"========== SHEET: {sheet_name} ==========",
            "",
            f"Rows: {len(df)}",
            f"Columns: {len(df.columns)}",
            "",
            "Columns:",
        ])


        # ----------------------------------------------------
        # Columns
        # ----------------------------------------------------

        for column in df.columns:

            output.append(
                f"- {column}"
            )


        # ----------------------------------------------------
        # Preview
        # ----------------------------------------------------

        output.extend([
            "",
            "Preview:",
            "",
        ])


        if df.empty:

            output.append(
                "This sheet is empty."
            )

        else:

            output.append(
                df.head(20).to_string(
                    index=False
                )
            )


        # ----------------------------------------------------
        # Numeric Summary
        # ----------------------------------------------------

        numeric_columns = (
            df.select_dtypes(
                include="number"
            ).columns
        )


        if len(numeric_columns) > 0:

            output.extend([
                "",
                "Numeric Summary:",
                "",
            ])


            output.append(
                df[numeric_columns]
                .describe()
                .to_string()
            )


    return "\n".join(output)


# ============================================================
# PDF
# ============================================================

def extract_pdf(filepath: str) -> str:
    """
    Extract text from every page of a PDF.
    """

    try:

        reader = PdfReader(
            filepath
        )

    except Exception as error:

        raise ValueError(
            f"Could not open PDF: {error}"
        ) from error


    if not reader.pages:
        return "The PDF file contains no pages."


    output = [
        "========== PDF DOCUMENT ==========",
        "",
    ]


    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        try:

            text = (
                page.extract_text()
                or ""
            )

        except Exception as error:

            text = (
                f"[Could not extract text "
                f"from page {page_number}: "
                f"{error}]"
            )


        output.extend([
            "",
            f"========== PAGE {page_number} ==========",
            "",
            text.strip(),
        ])


    return "\n".join(output)


# ============================================================
# TEXT
# ============================================================

def extract_text(filepath: str) -> str:
    """
    Read a plain-text file using common encodings.
    """

    encodings = (
        "utf-8",
        "utf-8-sig",
        "latin-1",
    )


    last_error = None


    for encoding in encodings:

        try:

            with open(
                filepath,
                "r",
                encoding=encoding
            ) as file:

                return file.read()

        except UnicodeDecodeError as error:

            last_error = error


    raise ValueError(
        "Could not decode text file."
    ) from last_error


# ============================================================
# MAIN FILE EXTRACTION
# ============================================================

def extract_file_content(filepath: str) -> str:
    """
    Route a file to the appropriate extractor based
    on its extension.
    """

    extension = (
        Path(filepath)
        .suffix
        .lower()
    )


    extractors = {

        ".csv":
            extract_csv,

        ".xlsx":
            extract_excel,

        ".xls":
            extract_excel,

        ".pdf":
            extract_pdf,

        ".txt":
            extract_text,

    }


    extractor = extractors.get(
        extension
    )


    if extractor is None:

        raise ValueError(
            f"File type '{extension or 'unknown'}' "
            "is not supported yet."
        )


    return extractor(
        filepath
    )