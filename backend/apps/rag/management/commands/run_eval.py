import datetime as dt
import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.rag.services.pipeline import RAGPipeline


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class Command(BaseCommand):
    help = (
        "Corre los casos dorados y adversariales (compartidos con ML/data/gold_cases) contra "
        "el pipeline RAG real y genera un reporte. Soporta el reto extra E4 (set de "
        "evaluación propio, min. 5 casos) mostrado en vivo durante la demo."
    )

    def add_arguments(self, parser):
        parser.add_argument("--out-dir", default="eval_reports")

    def handle(self, *args, **options):
        gold_cases = read_jsonl(settings.EVAL_GOLD_CASES_PATH)
        adversarial_cases = read_jsonl(settings.EVAL_ADVERSARIAL_CASES_PATH)
        all_cases = [(c, False) for c in gold_cases] + [(c, True) for c in adversarial_cases]

        if not all_cases:
            self.stderr.write(self.style.ERROR("No hay casos en ML/data/gold_cases/."))
            return

        pipeline = RAGPipeline()
        results = []
        for case, is_adversarial in all_cases:
            result = pipeline.answer(case.get("pregunta", ""))
            respuesta_lower = result.answer.lower()
            keywords = case.get("palabras_clave_esperadas", [])
            keyword_hits = [k for k in keywords if k.lower() in respuesta_lower]
            passed = result.out_of_domain if is_adversarial else bool(keyword_hits) or result.empty_input
            results.append(
                {
                    "id": case["id"],
                    "pregunta": case.get("pregunta", ""),
                    "es_adversarial": is_adversarial,
                    "out_of_domain": result.out_of_domain,
                    "keyword_hits": keyword_hits,
                    "citations": [f"{c['norma']} - {c['articulo']}" for c in result.citations],
                    "passed": passed,
                    "respuesta": result.answer,
                }
            )

        n_passed = sum(1 for r in results if r["passed"])
        out_dir = Path(options["out_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = out_dir / f"eval_{stamp}.json"
        report_path.write_text(
            json.dumps(
                {"total": len(results), "passed": n_passed, "results": results},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        for r in results:
            marker = self.style.SUCCESS("OK") if r["passed"] else self.style.ERROR("FAIL")
            self.stdout.write(f"[{marker}] {r['id']}: {r['pregunta'][:60]}")

        self.stdout.write(self.style.SUCCESS(f"\n{n_passed}/{len(results)} casos aprobados"))
        self.stdout.write(f"Reporte: {report_path}")
