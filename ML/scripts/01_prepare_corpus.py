"""Trocea /corpus en chunks por artículo y los guarda en JSONL para inspección rápida.

Uso:
    python scripts/01_prepare_corpus.py
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_CORPUS_DIR, ML_DIR, load_corpus, write_jsonl  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-dir", type=Path, default=DEFAULT_CORPUS_DIR)
    parser.add_argument("--out", type=Path, default=ML_DIR / "data" / "corpus" / "chunks.jsonl")
    args = parser.parse_args()

    if not args.corpus_dir.exists():
        raise SystemExit(
            f"No existe {args.corpus_dir}. Este script espera la carpeta /corpus en la raíz "
            "del repositorio (ver corpus/README.md)."
        )

    chunks = load_corpus(args.corpus_dir)
    if not chunks:
        raise SystemExit(f"No se encontraron chunks en {args.corpus_dir}. Revisa el formato de los .txt.")

    write_jsonl(args.out, [c.to_dict() for c in chunks])

    pendientes = [c for c in chunks if "RESUMEN" in c.text or "PENDIENTE" in c.text or c.estado != "verificado"]
    print(f"{len(chunks)} chunks escritos en {args.out}")
    print(f"{len(pendientes)} chunks marcados como pendientes/seed parcial (revisar antes del evento):")
    for c in pendientes:
        print(f"  - [{c.estado}] {c.norma} - {c.articulo} ({c.source_file})")


if __name__ == "__main__":
    main()
