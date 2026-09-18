"""Genera el texto formal de la solicitud de Habeas Data a partir del tipo elegido y los
campos capturados del usuario. El fundamento legal se extrae directamente del corpus
normativo (misma fuente que usa el chat RAG), así el documento generado también cumple con
el reto extra E2 (citas verificables: se citan artículos y se incluye el fragmento fuente)."""
from __future__ import annotations

import datetime

from apps.rag.services.ingest import load_corpus

from ..types import get_tipo_config

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def _find_fundamento(articulos_fundamento: list[str]) -> list[dict]:
    chunks = load_corpus()
    found = []
    for cita in articulos_fundamento:
        norma, _, articulo = cita.partition(" - ")
        norma, articulo = norma.strip(), articulo.strip()
        for c in chunks:
            if c.norma.strip() == norma and c.articulo.strip().lower() == articulo.lower():
                found.append({"norma": c.norma, "articulo": c.articulo, "texto": c.text, "url": c.url})
                break
        else:
            found.append({"norma": norma, "articulo": articulo, "texto": "(texto no indexado aún, verificar en /corpus)", "url": ""})
    return found


def _peticion_especifica(tipo: str, campos: dict) -> tuple[str, str]:
    """Devuelve (seccion_especifica, texto_peticion) según el tipo de solicitud."""
    if tipo == "consulta":
        info = campos.get("informacion_a_consultar", "").strip()
        seccion = f"Información puntual solicitada: {info}" if info else ""
        peticion = (
            "Solicito de manera respetuosa que me sea entregada toda la información personal "
            "que reposa en sus bases de datos o archivos relacionada conmigo, incluyendo el "
            "origen, uso y finalidad del tratamiento que se le ha dado."
        )
    elif tipo == "actualizacion":
        seccion = (
            f"Dato desactualizado o incompleto: {campos.get('dato_desactualizado', '')}\n"
            f"Información correcta y actual: {campos.get('informacion_correcta', '')}"
        )
        peticion = (
            "Solicito que actualicen el dato personal referido en la sección anterior, "
            "reemplazándolo por la información correcta y vigente que allí se indica."
        )
    elif tipo == "rectificacion":
        seccion = (
            f"Dato falso, inexacto o parcial: {campos.get('dato_incorrecto', '')}\n"
            f"Información correcta: {campos.get('informacion_correcta', '')}\n"
            f"Razón: {campos.get('razon', '')}"
        )
        peticion = (
            "Solicito que rectifiquen de manera inmediata el dato personal referido, "
            "corrigiéndolo conforme a la información correcta indicada."
        )
    elif tipo == "supresion":
        seccion = (
            f"Dato a suprimir: {campos.get('dato_a_suprimir', '')}\n"
            f"Razón de la supresión: {campos.get('razon_supresion', '')}"
        )
        peticion = (
            "Solicito la supresión (eliminación definitiva) del dato personal referido de sus "
            "bases de datos y archivos, por no respetar los principios y garantías legales "
            "aplicables al tratamiento de datos personales."
        )
    elif tipo == "revocatoria":
        seccion = (
            f"Finalidad autorizada que se revoca: {campos.get('finalidad_a_revocar', '')}\n"
            f"Fecha aproximada de la autorización: {campos.get('fecha_autorizacion', 'no especificada')}"
        )
        peticion = (
            "Por medio de la presente revoco la autorización otorgada previamente para el "
            "tratamiento de mis datos personales para la finalidad referida, y solicito que "
            "cesen dicho tratamiento a partir de la fecha de recibo de esta comunicación."
        )
    else:
        raise ValueError(f"Tipo de solicitud desconocido: {tipo}")
    return seccion, peticion


def build_document_text(tipo: str, campos: dict) -> str:
    cfg = get_tipo_config(tipo)
    fundamento = _find_fundamento(cfg["articulos_fundamento"])
    seccion_especifica, texto_peticion = _peticion_especifica(tipo, campos)

    hoy = datetime.date.today()
    fecha_texto = f"{hoy.day} de {MESES[hoy.month - 1]} de {hoy.year}"

    fundamento_lines = "\n".join(
        f"- {f['norma']}, {f['articulo']}: \"{' '.join(f['texto'].split())[:300]}\"" for f in fundamento
    )

    contacto = campos.get("correo_notificacion", "")
    if campos.get("telefono"):
        contacto += f" / {campos['telefono']}"

    partes = [
        f"{campos.get('ciudad', '')}, {fecha_texto}",
        "",
        "Señores",
        campos.get("entidad_destinataria", ""),
        campos.get("entidad_direccion_o_correo", ""),
        "",
        f"Asunto: {cfg['label']} de datos personales (Habeas Data)",
        "",
        (
            f"Yo, {campos.get('nombre_completo', '')}, identificado(a) con "
            f"{campos.get('tipo_documento_identidad', '')} No. {campos.get('numero_documento', '')}, "
            "en ejercicio del derecho fundamental al Habeas Data consagrado en el artículo 15 "
            "de la Constitución Política de Colombia y desarrollado por la Ley 1581 de 2012, "
            f"me dirijo respetuosamente a ustedes para presentar la siguiente {cfg['label'].lower()}."
        ),
        "",
        "HECHOS",
        campos.get("hechos", ""),
    ]
    if seccion_especifica:
        partes += ["", seccion_especifica]
    partes += [
        "",
        "PETICIÓN",
        texto_peticion,
        "",
        "FUNDAMENTO LEGAL",
        fundamento_lines,
        "",
        f"Les recuerdo que, de conformidad con el fundamento legal citado, el plazo legal para "
        f"atender esta solicitud es: {cfg['plazo_legal']}",
        "",
        f"Para efectos de notificación pueden contactarme a través de: {contacto}",
        "",
        "Atentamente,",
        "",
        campos.get("nombre_completo", ""),
        f"{campos.get('tipo_documento_identidad', '')} No. {campos.get('numero_documento', '')}",
        "",
        "---",
        (
            "Este documento fue generado por ProyectadurIA como borrador de apoyo y no "
            "sustituye la asesoría de un abogado. Revísalo y ajústalo antes de radicarlo."
        ),
    ]
    return "\n".join(partes)
