"""Clientes de LLM para la generación de respuestas del chat RAG.

Proveedor primario recomendado: Ollama, sirviendo el Qwen fine-tuneado en ML/ (100% local,
sin llave de API, cumple con el requisito de despliegue local). Si Ollama no está disponible
(por ejemplo durante desarrollo sin el modelo aún entrenado/registrado), se puede usar un
proveedor externo con capa gratuita (Gemini o Groq) configurando LLM_PROVIDER en el .env, y
opcionalmente un proveedor de respaldo con LLM_FALLBACK_PROVIDER.
"""
from __future__ import annotations

import abc
import json
import logging
from collections.abc import Iterator

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class LLMProvider(abc.ABC):
    name = "base"

    @abc.abstractmethod
    def generate(self, system: str, user_message: str) -> str:
        ...

    def generate_stream(self, system: str, user_message: str) -> Iterator[str]:
        """Implementación por defecto: sin streaming real del proveedor, se trocea la
        respuesta completa en palabras para dar una experiencia de streaming en el frontend
        (reto extra E9). Los proveedores que sí soportan streaming nativo (Ollama, Groq)
        sobreescriben este método con streaming real, token a token."""
        text = self.generate(system, user_message)
        for word in text.split(" "):
            yield word + " "


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, base_url: str | None = None, model: str | None = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    def _messages(self, system: str, user_message: str) -> list[dict]:
        return [{"role": "system", "content": system}, {"role": "user", "content": user_message}]

    def generate(self, system: str, user_message: str) -> str:
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": self._messages(system, user_message), "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["message"]["content"]

    def generate_stream(self, system: str, user_message: str) -> Iterator[str]:
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={"model": self.model, "messages": self._messages(system, user_message), "stream": True},
            timeout=120,
            stream=True,
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            content = data.get("message", {}).get("content", "")
            if content:
                yield content
            if data.get("done"):
                break


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY no configurada")

    def generate(self, system: str, user_message: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )
        body = {
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user_message}]}],
        }
        resp = requests.post(url, json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


class GroqProvider(LLMProvider):
    name = "groq"
    ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY no configurada")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _messages(self, system: str, user_message: str) -> list[dict]:
        return [{"role": "system", "content": system}, {"role": "user", "content": user_message}]

    def generate(self, system: str, user_message: str) -> str:
        resp = requests.post(
            self.ENDPOINT,
            headers=self._headers(),
            json={"model": self.model, "messages": self._messages(system, user_message), "stream": False},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def generate_stream(self, system: str, user_message: str) -> Iterator[str]:
        resp = requests.post(
            self.ENDPOINT,
            headers=self._headers(),
            json={"model": self.model, "messages": self._messages(system, user_message), "stream": True},
            timeout=60,
            stream=True,
        )
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line or not line.startswith(b"data: "):
                continue
            payload = line[len(b"data: "):]
            if payload.strip() == b"[DONE]":
                break
            delta = json.loads(payload)["choices"][0]["delta"].get("content", "")
            if delta:
                yield delta


def _build_provider(name: str) -> LLMProvider:
    if name == "ollama":
        return OllamaProvider()
    if name == "gemini":
        return GeminiProvider()
    if name == "groq":
        return GroqProvider()
    raise ValueError(f"Proveedor de LLM desconocido: {name}")


class CompositeLLMClient:
    """Intenta el proveedor primario y cae al de respaldo si el primero falla (p. ej. Ollama
    no está corriendo o el modelo aún no fue registrado)."""

    def __init__(self, primary: str | None = None, fallback: str | None = None):
        self.primary_name = primary or settings.LLM_PROVIDER
        self.fallback_name = fallback or settings.LLM_FALLBACK_PROVIDER

    def _provider(self, name: str) -> LLMProvider:
        return _build_provider(name)

    def generate(self, system: str, user_message: str) -> str:
        try:
            return self._provider(self.primary_name).generate(system, user_message)
        except Exception:
            logger.exception("Fallo el proveedor primario de LLM (%s), usando respaldo (%s)", self.primary_name, self.fallback_name)
            if not self.fallback_name or self.fallback_name == self.primary_name:
                raise
            return self._provider(self.fallback_name).generate(system, user_message)

    def generate_stream(self, system: str, user_message: str) -> Iterator[str]:
        try:
            provider = self._provider(self.primary_name)
            yield from provider.generate_stream(system, user_message)
        except Exception:
            logger.exception(
                "Fallo el streaming del proveedor primario (%s), usando respaldo (%s)",
                self.primary_name,
                self.fallback_name,
            )
            if not self.fallback_name or self.fallback_name == self.primary_name:
                raise
            yield from self._provider(self.fallback_name).generate_stream(system, user_message)


def get_llm_client() -> CompositeLLMClient:
    return CompositeLLMClient()
