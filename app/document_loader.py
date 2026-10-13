
from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


def load_document(uploaded_file):
    filename = Path(uploaded_file.name).name
    extension = Path(filename).suffix.lower()
    content = uploaded_file.getvalue()

    documents = []

    if extension == ".pdf":
        reader = PdfReader(BytesIO(content))

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                documents.append({
                    "text": text,
                    "source": filename,
                    "page": page_number,
                })

    elif extension == ".docx":
        document = Document(BytesIO(content))
        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )

        if text.strip():
            documents.append({
                "text": text,
                "source": filename,
                "page": None,
            })

    elif extension in {".txt", ".md"}:
        text = content.decode("utf-8-sig", errors="replace")

        if text.strip():
            documents.append({
                "text": text,
                "source": filename,
                "page": None,
            })

    else:
        raise ValueError(
            "Supported formats: PDF, DOCX, TXT and MD."
        )

    if not documents:
        raise ValueError(
            f"No readable text found in {filename}."
        )

    return documents
