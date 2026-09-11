"""Documentos → páginas → limpeza → chunks → JSONL."""
import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import sys
import tempfile

from ingestion.chunking.text_chunker import chunk_page, validate_chunk_settings
from ingestion.loaders.document_loader import SUPPORTED_SUFFIXES, load_document
from ingestion.models import Chunk, IngestionError


def ingest(root: Path, chunk_size: int = 800, overlap: int = 120) -> list[Chunk]:
    validate_chunk_settings(chunk_size, overlap)
    root = root.resolve()
    if not root.is_dir():
        raise IngestionError(f"Pasta de documentos não encontrada: {root}")
    paths = sorted(p for p in root.rglob("*")
                   if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES)
    if not paths:
        raise IngestionError("Nenhum arquivo TXT, Markdown ou PDF encontrado.")
    chunks = []
    for path in paths:
        for page in load_document(path, root):
            chunks.extend(chunk_page(page, chunk_size, overlap))
    if not chunks:
        raise IngestionError("A limpeza não produziu texto para gerar chunks.")
    return chunks


def write_jsonl(chunks: list[Chunk], output: Path) -> None:
    """Substitui o resultado somente após concluir a gravação."""
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=output.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            for chunk in chunks:
                stream.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
        os.replace(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fase 3: ingestão local para JSONL.")
    parser.add_argument("--documents", type=Path, default=Path("documents"))
    parser.add_argument("--output", type=Path, default=Path("data/chunks.jsonl"))
    parser.add_argument("--chunk-size", type=int, default=800, help="Tamanho em caracteres.")
    parser.add_argument("--overlap", type=int, default=120, help="Sobreposição em caracteres.")
    args = parser.parse_args()
    try:
        # Evita sobrescrever documentos de entrada, inclusive por symlink.
        if args.output.resolve().is_relative_to(args.documents.resolve()):
            raise IngestionError("O arquivo de saída deve ficar fora da pasta de documentos.")
        chunks = ingest(args.documents, args.chunk_size, args.overlap)
        write_jsonl(chunks, args.output)
    except (ValueError, OSError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1
    sources = {chunk.metadata["source"] for chunk in chunks}
    print(f"{len(sources)} documento(s) → {len(chunks)} chunks em {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
