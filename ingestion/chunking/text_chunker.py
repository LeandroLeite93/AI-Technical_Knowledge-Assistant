"""Janelas de caracteres com sobreposição; nunca cruzam páginas."""
import hashlib
import json

from ingestion.models import Chunk, Page
from ingestion.parsers.text_cleaner import clean_text


def validate_chunk_settings(chunk_size: int, overlap: int) -> None:
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Use chunk_size > 0 e 0 <= overlap < chunk_size.")


def chunk_page(page: Page, chunk_size: int = 800, overlap: int = 120) -> list[Chunk]:
    validate_chunk_settings(chunk_size, overlap)
    text = clean_text(page.text)
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        fragment = text[start:end]
        if fragment.strip():
            metadata = {
                "source": page.source, "page": page.page, "category": page.category,
                "chunk_index": len(chunks), "start_char": start, "end_char": end,
            }
            identity = json.dumps(
                [metadata, fragment], ensure_ascii=False, sort_keys=True
            ).encode("utf-8")
            chunks.append(Chunk(hashlib.sha256(identity).hexdigest(), fragment, metadata))
        if end == len(text):
            break
        start = end - overlap
    return chunks
