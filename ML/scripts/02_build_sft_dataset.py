"""Construye el dataset de instrucción (SFT) para fine-tunear Qwen a partir de:
- ML/data/gold_cases/gold_cases.jsonl (casos dentro de dominio)
- ML/data/gold_cases/adversarial_cases.jsonl (casos fuera de dominio / adversariales)
- /corpus (para armar el contexto recuperado simulado y citar normas reales)

Genera ejemplos en formato chat ({"messages": [...]}), listos para TRL SFTTrainer, y hace un
split train/val. El dataset semilla es pequeño (~18 casos): sirve para validar el pipeline de
entrenamiento de punta a punta, pero para resultados de calidad se debe ampliar
gold_cases.jsonl/adversarial_cases.jsonl con más ejemplos (idealmente 100+) antes del
entrenamiento final.

Uso:
    python scripts/02_build_sft_dataset.py
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    ADVERSARIAL_CASES_PATH,
    GOLD_CASES_PATH,
    SFT_DIR,
    Chunk,
    flatten_snippet,
    load_corpus,
    read_jsonl,
    write_jsonl,
)
from prompt_templates import DISCLAIMER, OUT_OF_DOMAIN_MESSAGE, SYSTEM_PROMPT  # noqa: E402

PASOS_HABEAS_DATA = {
    "consulta_habeas_data": [
        "Identifica ante quién presentas la solicitud: el responsable o encargado del "
        "tratamiento de tus datos (el banco, la entidad, la empresa).",
        "Redacta la petición de consulta indicando tu nombre completo, número de "
        "identificación y los datos que quieres consultar.",
        "Envíala por un medio que deje constancia (correo electrónico, radicado físico o "
        "formulario web con confirmación).",
        "Guarda la prueba de envío: el plazo legal para que te respondan es de 10 días "
        "hábiles desde la fecha de recibo.",
        "Si no responden en ese plazo, puedes presentar una queja ante la Superintendencia "
        "de Industria y Comercio.",
    ],
    "actualizacion_habeas_data": [
        "Identifica el dato exacto que está desactualizado o incompleto y ten a la mano la "
        "información correcta y vigente.",
        "Presenta un reclamo escrito ante el responsable del tratamiento pidiendo que "
        "actualicen ese dato, describiendo los hechos y adjuntando los soportes si los tienes.",
        "El responsable debe incluir la leyenda 'reclamo en trámite' en un máximo de 2 días "
        "hábiles tras recibir tu reclamo completo.",
        "El plazo legal para resolver el reclamo es de 15 días hábiles, prorrogables 8 días "
        "hábiles más si te informan el motivo.",
        "Si no actualizan el dato, puedes acudir a la Superintendencia de Industria y Comercio.",
    ],
    "rectificacion_habeas_data": [
        "Identifica el dato exacto que está incorrecto o desactualizado y consigue evidencia "
        "de cuál es el dato correcto.",
        "Presenta un reclamo escrito ante el responsable del tratamiento describiendo los "
        "hechos y adjuntando los soportes.",
        "El responsable debe incluir la leyenda 'reclamo en trámite' en un máximo de 2 días "
        "hábiles tras recibir tu reclamo completo.",
        "El plazo legal para resolver el reclamo es de 15 días hábiles, prorrogables 8 días "
        "hábiles más si te informan el motivo.",
        "Si no corrigen el dato, puedes acudir a la Superintendencia de Industria y Comercio.",
    ],
    "supresion_habeas_data": [
        "Verifica que se cumpla alguna causal de supresión: el dato ya no es necesario, "
        "venció el tiempo legal de conservación, o el tratamiento incumple los principios "
        "legales.",
        "Presenta un reclamo escrito solicitando expresamente la supresión (eliminación) del "
        "dato, no solo su corrección.",
        "El plazo legal para resolver el reclamo es de 15 días hábiles, prorrogables 8 días "
        "hábiles más.",
        "Si el dato está en una central de riesgo, ten en cuenta las reglas específicas de "
        "permanencia de la Ley 1266 de 2008 (verifícalas con la entidad o un abogado).",
        "Si no obtienes respuesta o la respuesta es negativa sin fundamento, puedes acudir a "
        "la Superintendencia de Industria y Comercio.",
    ],
    "revocatoria_habeas_data": [
        "Identifica exactamente para qué finalidad diste la autorización y a quién (el "
        "responsable del tratamiento).",
        "Presenta la solicitud de revocatoria de la autorización por escrito, indicando que "
        "retiras el consentimiento para el tratamiento de tus datos.",
        "Puedes revocar la autorización en cualquier momento; no requiere que exista un "
        "incumplimiento previo por parte de la entidad.",
        "Pide confirmación por escrito de que dejaron de usar tus datos para esa finalidad.",
        "Si continúan usando tus datos pese a la revocatoria, puedes presentar una queja ante "
        "la Superintendencia de Industria y Comercio.",
    ],
}

PASOS_GENERICOS = [
    "Recopila y organiza todos los documentos o evidencias relacionados con tu situación.",
    "Identifica claramente ante qué entidad o persona debes dirigir tu solicitud o reclamo.",
    "Redacta una comunicación formal describiendo los hechos y lo que solicitas, y consérvala "
    "con prueba de envío.",
    "Haz seguimiento al plazo legal de respuesta que aplique a tu caso.",
    "Si no obtienes respuesta o la respuesta vulnera tus derechos, considera acudir a la "
    "autoridad de control competente o a la acción de tutela.",
]


def find_chunks_for_citas(chunks: list[Chunk], debe_citar: list[str]) -> list[Chunk]:
    found = []
    for cita in debe_citar:
        norma, _, articulo = cita.partition(" - ")
        norma, articulo = norma.strip(), articulo.strip()
        for c in chunks:
            if c.norma.strip() == norma and c.articulo.strip().lower() == articulo.lower():
                found.append(c)
                break
    return found


def build_context_block(chunks: list[Chunk]) -> str:
    if not chunks:
        return "(No hay artículos recuperados relevantes para este caso.)"
    lines = ["Contexto normativo recuperado:"]
    for c in chunks:
        lines.append(f"- [{c.norma} - {c.articulo}] {flatten_snippet(c.text)}")
    return "\n".join(lines)


def build_gold_answer(case: dict, chunks: list[Chunk]) -> str:
    pasos = PASOS_HABEAS_DATA.get(case.get("tipo_esperado"), PASOS_GENERICOS)
    normas_lines = (
        "\n".join(f"- {c.norma}, {c.articulo}: \"{flatten_snippet(c.text, 300)}\"" for c in chunks)
        if chunks
        else "- (Citar aquí la norma aplicable una vez verificada en el corpus.)"
    )
    pasos_lines = "\n".join(f"{i}. {p}" for i, p in enumerate(pasos, start=1))
    return (
        f"**Resumen de la situación**\n"
        f"{case['notas']}\n\n"
        f"**Norma o normas aplicables**\n"
        f"{normas_lines}\n\n"
        f"**Pasos a seguir**\n"
        f"{pasos_lines}\n\n"
        f"**Aviso legal**\n"
        f"{DISCLAIMER}"
    )


def build_user_message(pregunta: str, context_block: str) -> str:
    if not pregunta.strip():
        return "(El usuario no escribió ninguna consulta.)"
    return f"Consulta del usuario: {pregunta}\n\n{context_block}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--val-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    chunks = load_corpus()
    gold_cases = read_jsonl(GOLD_CASES_PATH)
    adversarial_cases = read_jsonl(ADVERSARIAL_CASES_PATH)

    if not gold_cases and not adversarial_cases:
        raise SystemExit("No se encontraron casos en ML/data/gold_cases/. Nada que construir.")

    examples = []

    for case in gold_cases:
        pregunta = case.get("pregunta", "")
        if not pregunta.strip():
            assistant = "(No se recibió texto. Por favor escribe tu consulta para poder ayudarte.)"
            context_block = "(Sin contexto: la consulta llegó vacía.)"
        else:
            cited_chunks = find_chunks_for_citas(chunks, case.get("debe_citar", []))
            context_block = build_context_block(cited_chunks)
            assistant = build_gold_answer(case, cited_chunks)
        examples.append(
            {
                "id": case["id"],
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_message(pregunta, context_block)},
                    {"role": "assistant", "content": assistant},
                ],
            }
        )

    for case in adversarial_cases:
        pregunta = case.get("pregunta", "")
        context_block = "(Sin contexto: la consulta no pertenece al dominio del asistente.)"
        examples.append(
            {
                "id": case["id"],
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_message(pregunta, context_block)},
                    {"role": "assistant", "content": OUT_OF_DOMAIN_MESSAGE},
                ],
            }
        )

    random.Random(args.seed).shuffle(examples)
    n_val = max(1, int(len(examples) * args.val_ratio))
    val_examples, train_examples = examples[:n_val], examples[n_val:]

    write_jsonl(SFT_DIR / "train.jsonl", train_examples)
    write_jsonl(SFT_DIR / "val.jsonl", val_examples)
    print(f"train: {len(train_examples)} ejemplos -> {SFT_DIR / 'train.jsonl'}")
    print(f"val:   {len(val_examples)} ejemplos -> {SFT_DIR / 'val.jsonl'}")
    if len(examples) < 100:
        print(
            "\nDataset pequeño: amplía gold_cases.jsonl y adversarial_cases.jsonl "
            "(idealmente 100+ casos combinados) antes de entrenar en serio."
        )


if __name__ == "__main__":
    main()
