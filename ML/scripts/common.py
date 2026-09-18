"""Helpers compartidos por los scripts de ML. Sin dependencias pesadas (torch, etc.)."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = ML_DIR.parent
DEFAULT_CORPUS_DIR = REPO_ROOT / "corpus"
GOLD_CASES_PATH = ML_DIR / "data" / "gold_cases" / "gold_cases.jsonl"
ADVERSARIAL_CASES_PATH = ML_DIR / "data" / "gold_cases" / "adversarial_cases.jsonl"
SFT_DIR = ML_DIR / "data" / "sft"
MODELS_DIR = ML_DIR / "models"
EVAL_DIR = ML_DIR / "eval"

ARTICLE_HEADER_RE = re.compile(r"^###\s*(.+?)\s*$", re.MULTILINE)
METADATA_RE = re.compile(r"^([A-Z_]+):\s*(.*)$", re.MULTILINE)


@dataclass
class Chunk:
    text: str
    articulo: str
    norma: str
    fuente: str
    url: str
    estado: str
    source_file: str
    chunk_id: str = field(default="")

    def to_dict(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "articulo": self.articulo,
            "norma": self.norma,
            "fuente": self.fuente,
            "url": self.url,
            "estado": self.estado,
            "source_file": self.source_file,
        }


def flatten_snippet(text: str, max_chars: int = 400) -> str:
    """Normaliza saltos de línea de envoltura (word-wrap) del .txt fuente a espacios, para no
    cortar la cita a mitad de frase por tomar solo la primera línea física."""
    return " ".join(text.split())[:max_chars]


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    items = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def write_jsonl(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def parse_corpus_file(path: Path) -> list[Chunk]:
    """Parsea un .txt del corpus (ver corpus/README.md) en chunks por artículo.

    Este parser es intencionalmente idéntico en espíritu al usado por
    ``backend/apps/rag/services/ingest.py`` para que el dataset de entrenamiento/evaluación
    quede alineado con lo que el backend realmente indexa.
    """
    raw = path.read_text(encoding="utf-8")
    metadata = dict(METADATA_RE.findall(raw))
    norma = metadata.get("NORMA", path.stem)
    fuente = metadata.get("FUENTE", norma)
    url = metadata.get("URL", "")
    estado = metadata.get("ESTADO", "desconocido")

    body_start = raw.find("### ")
    body = raw[body_start:] if body_start != -1 else ""

    headers = list(ARTICLE_HEADER_RE.finditer(body))
    chunks: list[Chunk] = []
    for i, match in enumerate(headers):
        articulo = match.group(1).strip()
        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(body)
        text = body[start:end].strip()
        if not text:
            continue
        chunk_id = f"{path.stem}::{articulo}".replace(" ", "_")
        chunks.append(
            Chunk(
                text=text,
                articulo=articulo,
                norma=norma,
                fuente=fuente,
                url=url,
                estado=estado,
                source_file=str(path.relative_to(REPO_ROOT)),
                chunk_id=chunk_id,
            )
        )
    return chunks


def load_corpus(corpus_dir: Path = DEFAULT_CORPUS_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.rglob("*.txt")):
        chunks.extend(parse_corpus_file(path))
    return chunks
