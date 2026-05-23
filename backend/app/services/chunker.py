import re
import uuid


def clean_text(text: str) -> str:
    """Basic text cleaning"""
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\x00', '')
    text = text.replace('\r\n', '\n')
    text = text.strip()
    return text


def chunk_text(
    text: str,
    chunk_size: int = 300,
    overlap: int = 30
) -> list[dict]:
    """
    Split text into overlapping chunks by word count.

    chunk_size → words per chunk
    overlap    → words shared between consecutive chunks
                 helps preserve context at boundaries

    Returns list of dicts:
    [
        {
            "id": "unique-uuid",
            "content": "chunk text here",
            "index": 0
        },
        ...
    ]
    """
    text = clean_text(text)
    words = text.split()

    if not words:
        return []

    chunks = []
    start = 0
    index = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = " ".join(chunk_words)

        chunks.append({
            "id": str(uuid.uuid4()),
            "content": chunk_text,
            "index": index
        })

        # Move forward by chunk_size minus overlap
        start += chunk_size - overlap
        index += 1

    return chunks


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Extract text from plain text file"""
    return file_bytes.decode("utf-8", errors="ignore")


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF file"""
    import io
    from pypdf import PdfReader

    pdf = PdfReader(io.BytesIO(file_bytes))
    pages = []

    for page in pdf.pages:
        text = page.extract_text()
        if text:
            pages.append(text)

    return "\n".join(pages)


def extract_text(filename: str, file_bytes: bytes) -> str:
    """
    Route to correct extractor based on file type.
    Currently supports PDF and TXT.
    """
    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith(".txt"):
        return extract_text_from_txt(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")