from __future__ import annotations

from django.conf import settings

from .embeddings import EmbeddingProvider, get_embedding_provider
from .vectorstore import ChromaVectorStore, get_vectorstore


class Retriever:
    """Recupera los fragmentos normativos más relevantes para una consulta y los formatea
    como citas listas para mostrar en el chat (E2: citas verificables)."""

    def __init__(self, embedding_provider: EmbeddingProvider | None = None, vectorstore: ChromaVectorStore | None = None):
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.vectorstore = vectorstore or get_vectorstore()

    def retrieve(self, query: str, top_k: int | None = None) -> list[dict]:
        top_k = top_k or settings.RAG_TOP_K
        query_embedding = self.embedding_provider.embed_one(query)
        results = self.vectorstore.query(query_embedding, top_k)
        citations = []
        for r in results:
            meta = r["metadata"]
            citations.append(
                {
                    "norma": meta.get("norma", ""),
                    "articulo": meta.get("articulo", ""),
                    "fuente": meta.get("fuente", ""),
                    "url": meta.get("url", ""),
                    "texto": r["text"],
                    "score": r["score"],
                }
            )
        return citations
