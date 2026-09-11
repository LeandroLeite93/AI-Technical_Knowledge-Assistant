"""Extrai TXT/Markdown UTF-8 e texto de PDF, mantendo páginas físicas."""
from pathlib import Path
import warnings

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from ingestion.models import IngestionError, Page

SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}


def load_document(path: Path, root: Path) -> list[Page]:
    path, root = path.resolve(), root.resolve()
    if not path.is_relative_to(root):
        raise IngestionError(f"Arquivo fora da pasta de documentos: {path.name}")
    relative = path.relative_to(root)
    source = relative.as_posix()
    category = relative.parts[0].upper() if len(relative.parts) > 1 else "GENERAL"
    if path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise IngestionError(f"Formato não suportado: {source}")
    try:
        if path.suffix.lower() != ".pdf":
            text = path.read_text(encoding="utf-8-sig")
            pages = [Page(text, source, None, category)]
        else:
            # Mantém o arquivo aberto durante a extração, mas o fecha em caso de falha.
            with path.open("rb") as stream:
                reader = PdfReader(stream)
                if reader.is_encrypted:
                    raise IngestionError(f"PDF protegido não suportado: {source}")
                pages = [
                    Page(page.extract_text() or "", source, index, category)
                    for index, page in enumerate(reader.pages, start=1)
                ]
    except (OSError, UnicodeError, PyPdfError) as exc:
        raise IngestionError(f"Falha ao ler {source}: {exc}") from exc
    nonempty = []
    for page in pages:
        if page.text.strip():
            nonempty.append(page)
        else:
            if page.page is not None:
                warnings.warn(
                    f"{source}, página {page.page}: sem texto extraível; "
                    "página vazia ou PDF pode precisar de OCR.",
                    UserWarning, stacklevel=2,
                )
    if not nonempty:
        hint = " OCR não implementado." if path.suffix.lower() == ".pdf" else ""
        raise IngestionError(f"Documento sem texto extraível: {source}.{hint}")
    return nonempty
