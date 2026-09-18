"""Fusiona el adaptador LoRA con el modelo base y deja el modelo listo para servir con Ollama.

Este script hace la parte que SÍ puede hacer en Python (merge del adaptador + guardar
safetensors). La conversión final a GGUF requiere `llama.cpp` (convert_hf_to_gguf.py) o el
propio `ollama create` a partir de un checkpoint HF reciente; el script imprime los comandos
exactos a ejecutar porque esas herramientas son binarios externos, no paquetes de pip.

Uso:
    python scripts/04_merge_and_export.py \
        --adapter models/qwen-proyectaduria-lora \
        --base-model Qwen/Qwen2.5-1.5B-Instruct \
        --out models/qwen-proyectaduria-merged
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import MODELS_DIR  # noqa: E402

MODELFILE_TEMPLATE = """FROM {gguf_path}

TEMPLATE \"\"\"{{{{ if .System }}}}<|im_start|>system
{{{{ .System }}}}<|im_end|>
{{{{ end }}}}{{{{ if .Prompt }}}}<|im_start|>user
{{{{ .Prompt }}}}<|im_end|>
<|im_start|>assistant
{{{{ end }}}}{{{{ .Response }}}}<|im_end|>
\"\"\"

PARAMETER stop <|im_start|>
PARAMETER stop <|im_end|>
PARAMETER temperature 0.3
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, required=True, help="Carpeta con el adaptador LoRA entrenado")
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--out", type=Path, default=MODELS_DIR / "qwen-proyectaduria-merged")
    parser.add_argument("--gguf-out", type=Path, default=MODELS_DIR / "gguf")
    args = parser.parse_args()

    if not args.adapter.exists():
        raise SystemExit(f"No existe {args.adapter}. Corre primero 03_train_qwen_lora.py")

    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"Cargando modelo base {args.base_model} y fusionando adaptador {args.adapter}...")
    base_model = AutoModelForCausalLM.from_pretrained(args.base_model, trust_remote_code=True)
    model = PeftModel.from_pretrained(base_model, str(args.adapter))
    merged = model.merge_and_unload()

    args.out.mkdir(parents=True, exist_ok=True)
    merged.save_pretrained(str(args.out), safe_serialization=True)
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    tokenizer.save_pretrained(str(args.out))
    print(f"Modelo fusionado guardado en {args.out}")

    args.gguf_out.mkdir(parents=True, exist_ok=True)
    modelfile_path = args.gguf_out / "Modelfile"
    gguf_file = args.gguf_out / "proyectaduria-qwen.Q4_K_M.gguf"
    modelfile_path.write_text(MODELFILE_TEMPLATE.format(gguf_path=gguf_file.name), encoding="utf-8")

    print("\nPasos manuales restantes (requieren llama.cpp, no son paquetes de pip):")
    print("  1. Clonar/instalar llama.cpp: https://github.com/ggerganov/llama.cpp")
    print(
        "  2. Convertir a GGUF:\n"
        f"     python convert_hf_to_gguf.py {args.out} --outfile {gguf_file} --outtype q4_k_m"
    )
    print(f"  3. Se generó un Modelfile de ejemplo en {modelfile_path}")
    print(
        "  4. Registrar el modelo en Ollama:\n"
        f"     ollama create proyectaduria-qwen -f {modelfile_path}"
    )
    print(
        "\nAlternativa sin llama.cpp: servir el modelo fusionado directamente con "
        "transformers/vLLM en el backend (más pesado, pero sin pasos de conversión manual). "
        "Ver backend/apps/rag/services/llm_client.py para el switch de proveedor."
    )


if __name__ == "__main__":
    main()
