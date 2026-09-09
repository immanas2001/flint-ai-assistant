from PyPDF2 import PdfReader


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from a PDF file.
    """

    try:
        reader = PdfReader(file_path)

        text = ""

        for page in reader.pages:
            page_text = page.extract_text()

            if page_text:
                text += page_text + "\n"

        return text.strip()

    except Exception as e:
        raise Exception(f"Error reading PDF: {e}")