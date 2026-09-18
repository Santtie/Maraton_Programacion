"""Proveedores de embeddings para la base vectorial del RAG.

Por defecto usa sentence-transformers en local (sin llaves de API, sin internet una vez
descargado el modelo la primera vez), tal como recomienda el enunciado del maratón para
corpus pequeños. Se puede cambiar a Gemini embeddings con RAG_EMBEDDING_PROVIDER=gemini.
"""
from __future__ import annotations

import abc
import functools

import requests
from django.conf import settings


class EmbeddingProvider(abc.ABC):
    @abc.abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]


class LocalSentenceTransformerEmbeddings(EmbeddingProvider):
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.RAG_EMBEDDING_MODEL
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(list(texts), normalize_embeddings=True).tolist()


class GeminiEmbeddings(EmbeddingProvider):
    """Usa el endpoint de embeddings de Google AI Studio (capa gratuita). Requiere
    GEMINI_API_KEY. Ver https://aistudio.google.com/."""

    ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY no configurada; no se puede usar RAG_EMBEDDING_PROVIDER=gemini")

    def embed(self, texts: list[str]) -> list[list[float]]:
        out = []
        for text in texts:
            resp = requests.post(
                f"{self.ENDPOINT}?key={self.api_key}",
                json={"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}},
                timeout=30,
            )
            resp.raise_for_status()
            out.append(resp.json()["embedding"]["values"])
        return out


@functools.lru_cache(maxsize=1)
def get_embedding_provider() -> EmbeddingProvider:
    provider = settings.RAG_EMBEDDING_PROVIDER
    if provider == "gemini":
        return GeminiEmbeddings()
    return LocalSentenceTransformerEmbeddings()
