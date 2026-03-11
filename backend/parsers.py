"""Utilities to extract plain text from various input formats."""

import re
import requests
from bs4 import BeautifulSoup


def parse_text(text: str) -> str:
    return text.strip()


def parse_pdf(file_bytes: bytes) -> str:
    import fitz  # pymupdf
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    pages = [page.get_text() for page in doc]
    return "\n\n".join(pages).strip()


def parse_docx(file_bytes: bytes) -> str:
    import io
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs).strip()


def parse_url(url: str) -> tuple[str, str]:
    """Returns (title, text)."""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; SaliencyBot/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    title = soup.title.string.strip() if soup.title else url

    # Remove boilerplate tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    # Clean up whitespace
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    return title, "\n".join(lines)
