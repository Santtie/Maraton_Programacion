"""Evalúa un modelo servido (Ollama u otro proveedor HTTP) contra gold_cases.jsonl y
adversarial_cases.jsonl. Verificación superficial (palabras clave / reconocimiento de fuera de
dominio), pensada para dar evidencia rápida y reproducible en la demo (reto extra E4) y no
para reemplazar una revisión legal humana.

Uso:
    # Por defecto usa Ollama en localhost:11434
    python scripts/05_evaluate.py --provider ollama --model proyectaduria-qwen

    # O contra un modelo base sin fine-tunear, para comparar
    python scripts/05_evaluate.py --provider ollama --model qwen2.5:1.5b
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ADVERSARIAL_CASES_PATH, EVAL_DIR, GOLD_CASES_PATH, flatten_snippet, load_corpus, read_jsonl  # noqa: E402
from prompt_templates import OUT_OF_DOMAIN_MESSAGE, SYSTEM_PROMPT  # noqa: E402


def call_ollama(model: str, base_url: str, system: str, user: str) -> str:
    resp = requests.post(
        f"{base_url}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def build_context(case: dict, chunks) -> str:
    debe_citar = case.get("debe_citar", [])
    if not debe_citar:
        return "(Sin contexto recuperado para este caso.)"
    lines = ["Contexto normativo recuperado:"]
    for cita in debe_citar:
        norma, _, articulo = cita.partition(" - ")
        for c in chunks:
            if c.norma.strip() == norma.strip() and c.articulo.strip().lower() == articulo.strip().lower():
                lines.append(f"- [{c.norma} - {c.articulo}] {flatten_snippet(c.text, 300)}")
                break
    return "\n".join(lines)


def evaluate_case(case: dict, respuesta: str, is_adversarial: bool) -> dict:
    respuesta_lower = respuesta.lower()
    keywords = case.get("palabras_clave_esperadas", [])
    keyword_hits = [k for k in keywords if k.lower() in respuesta_lower]
    declared_out_of_domain = any(
        marker in respuesta_lower for marker in ["fuera de mi dominio", "no puedo ayudarte con eso"]
    )
    passed = bool(keyword_hits) or (is_adversarial and declared_out_of_domain)
    if is_adversarial:
        passed = declared_out_of_domain
    return {
        "id": case["id"],
        "pregunta": case["pregunta"],
        "es_adversarial": is_adversarial,
        "keyword_hits": keyword_hits,
        "declared_out_of_domain": declared_out_of_domain,
        "passed": passed,
        "respuesta": respuesta,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", choices=["ollama"], default="ollama")
    parser.add_argument("--model", default="proyectaduria-qwen")
    parser.add_argument("--base-url", default="http://localhost:11434")
    args = parser.parse_args()

    chunks = load_corpus()
    gold_cases = read_jsonl(GOLD_CASES_PATH)
    adversarial_cases = read_jsonl(ADVERSARIAL_CASES_PATH)
    all_cases = [(c, False) for c in gold_cases] + [(c, True) for c in adversarial_cases]

    if not all_cases:
        raise SystemExit("No hay casos en ML/data/gold_cases/. Nada que evaluar.")

    results = []
    for case, is_adversarial in all_cases:
        pregunta = case.get("pregunta", "")
        if not pregunta.strip():
            user_msg = "(El usuario no escribió ninguna consulta.)"
        else:
            context = build_context(case, chunks)
            user_msg = f"Consulta del usuario: {pregunta}\n\n{context}"
        try:
            respuesta = call_ollama(args.model, args.base_url, SYSTEM_PROMPT, user_msg)
        except requests.exceptions.RequestException as exc:
            respuesta = f"[ERROR llamando al modelo: {exc}]"
        results.append(evaluate_case(case, respuesta, is_adversarial))

    n_passed = sum(1 for r in results if r["passed"])
    summary = {
        "model": args.model,
        "provider": args.provider,
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "total": len(results),
        "passed": n_passed,
        "accuracy": round(n_passed / len(results), 3),
        "results": results,
    }

    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = EVAL_DIR / f"eval_{stamp}.json"
    md_path = EVAL_DIR / f"eval_{stamp}.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        f"# Reporte de evaluación — {args.model} ({summary['timestamp']})",
        "",
        f"**Resultado global: {n_passed}/{len(results)} ({summary['accuracy']:.1%})**",
        "",
        "| Caso | Adversarial | Passed | Fuera de dominio declarado | Keywords encontradas |",
        "|---|---|---|---|---|",
    ]
    for r in results:
        md_lines.append(
            f"| {r['id']} | {r['es_adversarial']} | {'OK' if r['passed'] else 'FAIL'} | "
            f"{r['declared_out_of_domain']} | {', '.join(r['keyword_hits']) or '-'} |"
        )
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Resultado: {n_passed}/{len(results)} ({summary['accuracy']:.1%})")
    print(f"Reporte: {json_path}")
    print(f"Reporte: {md_path}")


if __name__ == "__main__":
    main()
