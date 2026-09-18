"""Renderiza el texto de la solicitud de Habeas Data a PDF (reto extra E7). Usa xhtml2pdf
(puro Python, sin dependencias de sistema como GTK/Cairo, por lo que instala igual en
Windows, Linux y macOS)."""
from __future__ import annotations

import datetime
import io

from django.template.loader import render_to_string
from xhtml2pdf import pisa

from ..types import get_tipo_config


def render_pdf(tipo: str, texto: str) -> bytes:
    cfg = get_tipo_config(tipo)
    html = render_to_string(
        "documents/habeas_data.html",
        {
            "tipo_label": cfg["label"],
            "texto": texto,
            "generado_en": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        },
    )
    buffer = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer)
    if result.err:
        raise RuntimeError("No se pudo generar el PDF de la solicitud de Habeas Data")
    return buffer.getvalue()
