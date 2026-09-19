"""Fine-tuning LoRA/QLoRA de un modelo Qwen2.5-Instruct sobre el dataset SFT generado por
02_build_sft_dataset.py.

Requiere GPU para tiempos de entrenamiento razonables (en CPU corre pero muy lento). Si hay
GPU con poca VRAM, usa --load-in-4bit para QLoRA.

Uso:
    python scripts/03_train_qwen_lora.py \
        --base-model Qwen/Qwen2.5-1.5B-Instruct \
        --epochs 3 \
        --out models/qwen-proyectaduria-lora
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import MODELS_DIR, SFT_DIR  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--train-file", type=Path, default=SFT_DIR / "train.jsonl")
    parser.add_argument("--val-file", type=Path, default=SFT_DIR / "val.jsonl")
    parser.add_argument("--out", type=Path, default=MODELS_DIR / "qwen-proyectaduria-lora")
    parser.add_argument("--epochs", type=float, default=3.0)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--max-seq-len", type=int, default=2048)
    parser.add_argument("--load-in-4bit", action="store_true", help="QLoRA (recomendado en GPU <=8GB VRAM)")
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    args = parser.parse_args()

    if not args.train_file.exists():
        raise SystemExit(f"No existe {args.train_file}. Corre primero 02_build_sft_dataset.py")

    # Imports pesados solo aquí, para que --help y el resto de scripts no requieran torch instalado.
    import torch
    from datasets import load_dataset
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    print(f"Cargando tokenizer/modelo base: {args.base_model}")
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quant_config = None
    if args.load_in_4bit:
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
        )

    # El parámetro device_map (tanto "auto" como un dict fijo como {"": 0}) dispara la lógica
    # de dispatch de `accelerate`, que en esta máquina (Windows + esta combinación de
    # versiones de torch/accelerate/transformers) provoca un segmentation fault nativo -salvo
    # cuando se usa cuantización con bitsandbytes, que tiene su propio camino de carga y sí
    # requiere device_map-. Por eso: con --load-in-4bit se pasa device_map={"": 0}; sin
    # cuantizar, se carga el modelo sin device_map (todo a CPU) y se mueve a la GPU a mano con
    # .to(), evitando por completo esa ruta de accelerate.
    if quant_config is not None:
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            trust_remote_code=True,
            quantization_config=quant_config,
            torch_dtype=torch.bfloat16,
            device_map={"": 0},
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            trust_remote_code=True,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        )
        if torch.cuda.is_available():
            model = model.to("cuda")

    lora_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    dataset = load_dataset(
        "json",
        data_files={"train": str(args.train_file), "validation": str(args.val_file)},
    )

    def formatting_func(example: dict) -> str:
        return tokenizer.apply_chat_template(example["messages"], tokenize=False, add_generation_prompt=False)

    sft_config = SFTConfig(
        output_dir=str(args.out),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        max_length=args.max_seq_len,
        logging_steps=5,
        eval_strategy="epoch",
        save_strategy="epoch",
        bf16=torch.cuda.is_available(),
        report_to=[],
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=dataset["train"],
        eval_dataset=dataset["validation"],
        formatting_func=formatting_func,
    )
    trainer.train()

    args.out.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(args.out))
    tokenizer.save_pretrained(str(args.out))
    print(f"Adaptador LoRA guardado en {args.out}")
    print("Siguiente paso: python scripts/04_merge_and_export.py --adapter "
          f"{args.out} --base-model {args.base_model}")


if __name__ == "__main__":
    main()
