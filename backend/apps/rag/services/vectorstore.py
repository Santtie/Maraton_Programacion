"""Envoltorio delgado sobre ChromaDB (persistente en disco, embebido, sin servidor aparte)."""
from __future__ import annotations

import functools

from django.conf import settings

COLLECTION_NAME = "corpus_derechos_fundamentales"


class ChromaVectorStore:
    def __init__(self, persist_dir: str | None = None, collection_name: str = COLLECTION_NAME):
        import chromadb

        self.persist_dir = persist_dir or settings.RAG_CHROMA_DIR
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(collection_name)

    def reset(self) -> None:
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(self.collection.name)

    def count(self) -> int:
        return self.collection.count()

    def upsert(self, ids: list[str], texts: list[str], metadatas: list[dict], embeddings: list[list[float]]) -> None:
        self.collection.upsert(ids=ids, documents=texts, metadatas=metadatas, embeddings=embeddings)

    def query(self, query_embedding: list[float], top_k: int) -> list[dict]:
        if self.collection.count() == 0:
            return []
        result = self.collection.query(query_embeddings=[query_embedding], n_results=min(top_k, self.collection.count()))
        out = []
        for text, metadata, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        ):
            # Chroma usa distancia (menor = más similar) sobre embeddings normalizados;
            # la convertimos a un score de similitud en [0, 1] aproximado.
            score = max(0.0, 1.0 - distance / 2.0)
            out.append({"text": text, "metadata": metadata, "score": score})
        return out


@functools.lru_cache(maxsize=1)
def get_vectorstore() -> ChromaVectorStore:
    return ChromaVectorStore()
