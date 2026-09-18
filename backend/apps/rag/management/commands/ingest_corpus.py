from django.conf import settings
from django.core.management.base import BaseCommand

from apps.rag.services.embeddings import get_embedding_provider
from apps.rag.services.ingest import load_corpus
from apps.rag.services.vectorstore import get_vectorstore


class Command(BaseCommand):
    help = "Trocea /corpus por artículo, genera embeddings y los indexa en ChromaDB (E1: RAG con corpus propio)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Vacía la colección antes de indexar")

    def handle(self, *args, **options):
        chunks = load_corpus()
        if not chunks:
            self.stderr.write(self.style.ERROR(f"No se encontraron chunks en {settings.RAG_CORPUS_DIR}"))
            return

        store = get_vectorstore()
        if options["reset"]:
            store.reset()
            self.stdout.write("Colección reiniciada.")

        embedder = get_embedding_provider()
        self.stdout.write(f"Generando embeddings para {len(chunks)} chunks (proveedor: {settings.RAG_EMBEDDING_PROVIDER})...")
        embeddings = embedder.embed([c.text for c in chunks])

        store.upsert(
            ids=[c.chunk_id for c in chunks],
            texts=[c.text for c in chunks],
            metadatas=[c.as_metadata() for c in chunks],
            embeddings=embeddings,
        )

        pendientes = [c for c in chunks if c.estado != "verificado"]
        self.stdout.write(self.style.SUCCESS(f"Indexados {len(chunks)} chunks en {settings.RAG_CHROMA_DIR}"))
        if pendientes:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(pendientes)} chunks siguen marcados como seed parcial/pendiente. "
                    "Revisa corpus/README.md antes del evento."
                )
            )
