"""Orquestador del RAG: recupera contexto normativo, filtra ruido evidente y genera la
respuesta (con o sin streaming), siempre devolviendo las citas usadas.

La clasificación fina dentro/fuera de dominio la hace el LLM (ver prompts.py); este módulo
solo hace de "fast path" para entradas vacías o claramente sin sentido, y post-procesa la
respuesta del LLM para detectar cuándo declaró la consulta fuera de dominio."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from . import domain_guard, prompts
from .llm_client import CompositeLLMClient, get_llm_client
from .retriever import Retriever


@dataclass
class RAGAnswer:
    answer: str
    citations: list[dict] = field(default_factory=list)
    out_of_domain: bool = False
    empty_input: bool = False


class RAGPipeline:
    def __init__(self, retriever: Retriever | None = None, llm_client: CompositeLLMClient | None = None):
        self.retriever = retriever or Retriever()
        self.llm_client = llm_client or get_llm_client()

    def answer(self, query: str, history: list[dict] | None = None) -> RAGAnswer:
        if not query.strip():
            return RAGAnswer(answer=prompts.EMPTY_INPUT_MESSAGE, empty_input=True)

        citations = self.retriever.retrieve(query)
        if domain_guard.is_probably_noise(query, citations):
            return RAGAnswer(answer=prompts.OUT_OF_DOMAIN_MESSAGE, citations=[], out_of_domain=True)

        user_message = prompts.build_user_message(query, citations)
        text = self.llm_client.generate(prompts.SYSTEM_PROMPT, user_message)

        if prompts.is_out_of_domain_response(text):
            return RAGAnswer(answer=prompts.OUT_OF_DOMAIN_MESSAGE, citations=[], out_of_domain=True)
        return RAGAnswer(answer=text, citations=citations)

    def stream_answer(self, query: str, history: list[dict] | None = None) -> Iterator[dict]:
        """Generador de eventos para SSE (reto extra E9). Cada evento es un dict:
        {"type": "token", "text": ...} mientras llegan tokens, y al final
        {"type": "done", "citations": [...], "out_of_domain": bool, "empty_input": bool}.

        Nota: como la detección de "fuera de dominio" depende del texto completo generado
        (ver prompts.is_out_of_domain_response), en el caso límite en que el LLM sí decide
        declarar la consulta fuera de dominio, los tokens ya se transmitieron al cliente antes
        de poder saberlo con certeza; el evento final igual corrige `out_of_domain` y limpia
        las citas para que la UI pueda re-renderizar el mensaje con el estilo adecuado."""
        if not query.strip():
            yield {"type": "token", "text": prompts.EMPTY_INPUT_MESSAGE}
            yield {"type": "done", "citations": [], "out_of_domain": False, "empty_input": True}
            return

        citations = self.retriever.retrieve(query)
        if domain_guard.is_probably_noise(query, citations):
            yield {"type": "token", "text": prompts.OUT_OF_DOMAIN_MESSAGE}
            yield {"type": "done", "citations": [], "out_of_domain": True, "empty_input": False}
            return

        user_message = prompts.build_user_message(query, citations)
        full_text = []
        for chunk in self.llm_client.generate_stream(prompts.SYSTEM_PROMPT, user_message):
            full_text.append(chunk)
            yield {"type": "token", "text": chunk}

        out_of_domain = prompts.is_out_of_domain_response("".join(full_text))
        yield {
            "type": "done",
            "citations": [] if out_of_domain else citations,
            "out_of_domain": out_of_domain,
            "empty_input": False,
        }
