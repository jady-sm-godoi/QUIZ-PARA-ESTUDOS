from PyPDF2 import PdfReader
from io import BytesIO


def extract_text_from_pdf(content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(content))
        text_parts = []

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

        return "\n\n".join(text_parts)
    except Exception as e:
        return ""


def is_pdf(content: bytes) -> bool:
    return content[:5] == b'%PDF-'


def extract_text(content: bytes, filename: str = "") -> str:
    if is_pdf(content):
        text = extract_text_from_pdf(content)
        if text.strip():
            return text

    try:
        return content.decode("utf-8", errors="ignore")
    except:
        return ""