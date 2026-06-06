import io
import re

from docx import Document
import pdfplumber


def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


def extract_text_from_pdf(file_bytes: bytes) -> str:
    pages = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
    return "\n".join(pages)


def extract_text(filename: str, file_bytes: bytes) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "docx":
        raw = extract_text_from_docx(file_bytes)
    elif ext == "pdf":
        raw = extract_text_from_pdf(file_bytes)
    else:
        raise ValueError(f"Unsupported file format: .{ext}. Use DOCX or PDF.")
    text = re.sub(r"\s+", " ", raw).strip()
    if len(text.split()) < 10:
        raise ValueError("Could not extract meaningful text from the uploaded file.")
    return text
