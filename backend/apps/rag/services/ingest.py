"""Parseo del corpus normativo (/corpus) en chunks por artículo.

Este parser espera el mismo formato descrito en corpus/README.md y es deliberadamente
equivalente al de ``ML/scripts/common.py`` (parse_corpus_file) para que lo que se entrena/
evalúa en ML/ y lo que se indexa aquí queden alineados.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

ARTICLE_HEADER_RE = re.compile(r"^###\s*(.+?)\s*$", re.MULTILINE)
METADATA_RE = re.compile(r"^([A-Z_]+):\s*(.*)$", re.MULTILINE)


@dataclass
class CorpusChunk:
    chunk_id: str
    text: str
    articulo: str
    norma: str
    fuente: str
    url: str
    estado: str
    source_file: str

    def as_metadata(self) -> dict:
        return {
            "articulo": self.articulo,
            "norma": self.norma,
            "fuente": self.fuente,
            "url": self.url,
            "estado": self.estado,
            "source_file": self.source_file,
        }


def parse_corpus_file(path: Path) -> list[CorpusChunk]:
    raw = path.read_text(encoding="utf-8")
    metadata = dict(METADATA_RE.findall(raw))
    norma = metadata.get("NORMA", path.stem)
    fuente = metadata.get("FUENTE", norma)
    url = metadata.get("URL", "")
    estado = metadata.get("ESTADO", "desconocido")

    body_start = raw.find("### ")
    body = raw[body_start:] if body_start != -1 else ""

    headers = list(ARTICLE_HEADER_RE.finditer(body))
    chunks: list[CorpusChunk] = []
    for i, match in enumerate(headers):
        articulo = match.group(1).strip()
        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(body)
        text = body[start:end].strip()
        if not text:
            continue
        chunk_id = f"{path.stem}::{articulo}".replace(" ", "_")
        chunks.append(
            CorpusChunk(
                chunk_id=chunk_id,
                text=text,
                articulo=articulo,
                norma=norma,
                fuente=fuente,
                url=url,
                estado=estado,
                source_file=str(path),
            )
        )
    return chunks


def load_corpus(corpus_dir: Path | None = None) -> list[CorpusChunk]:
    corpus_dir = corpus_dir or settings.RAG_CORPUS_DIR
    chunks: list[CorpusChunk] = []
    for path in sorted(Path(corpus_dir).rglob("*.txt")):
        chunks.extend(parse_corpus_file(path))
    return chunks
