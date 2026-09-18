"""Guardián de dominio (reto extra E5).

Diagnóstico empírico (ver nota de diseño en prompts.py): con el corpus real indexado, la
similitud de embeddings entre una consulta y los fragmentos legales NO separa de forma
confiable consultas dentro y fuera del dominio elegido (Derechos Fundamentales, Protección
de Datos e Intimidad). Consultas claramente ajenas como "me estafaron comprando un carro
usado" obtuvieron scores similares o mayores que consultas legítimas del dominio expresadas
en lenguaje natural sin vocabulario jurídico.

Por eso este módulo NO decide "dentro/fuera de dominio": solo detecta **ruido evidente**
(texto sin ninguna señal léxica ni semántica de pertenecer al dominio) para evitar gastar una
llamada al LLM en algo claramente vacío de contenido. La clasificación fina fuera/dentro de
dominio la hace el LLM, siguiendo la regla 1 del system prompt, y el pipeline la detecta
post-hoc comparando la respuesta contra el texto canónico de rechazo
(``prompts.is_out_of_domain_response``).
"""
from __future__ import annotations

from django.conf import settings

from .prompts import DOMAIN_KEYWORDS


def matches_domain_keywords(query: str) -> bool:
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in DOMAIN_KEYWORDS)


def is_probably_noise(query: str, citations: list[dict]) -> bool:
    """True solo para entradas sin ninguna señal de pertenecer al dominio: sin coincidencia
    de palabras clave y con una similitud de recuperación muy baja (p. ej. texto ininteligible
    o completamente ajeno a cualquier lenguaje jurídico)."""
    if matches_domain_keywords(query):
        return False
    best_score = max((c["score"] for c in citations), default=0.0)
    return best_score < settings.RAG_DOMAIN_SCORE_THRESHOLD
