"""Objetos compartilhados pelas etapas de ingestão."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Page:
    text: str
    source: str
    page: int | None
    category: str


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    metadata: dict[str, str | int | None]


class IngestionError(ValueError):
    """Arquivo que não pôde ser ingerido."""
