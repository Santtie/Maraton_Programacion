# ML — ProyectadurIA

Esta carpeta es independiente de `backend/` y `frontend/`. Aquí se preparan los datos y se
entrena/exporta el modelo (Qwen fine-tuneado) que luego el backend sirve **en local** (vía
Ollama) dentro de la arquitectura RAG. La arquitectura RAG en sí (retrieval, prompts,
generación en tiempo real, citas) vive en `backend/apps/rag` — esta carpeta solo produce el
modelo y los datasets de evaluación/entrenamiento.

## Por qué fine-tunear en vez de solo hacer prompting

El RAG (retrieval + prompt con contexto normativo) ya resuelve la mayoría de la calidad de
respuesta. El fine-tuning de Qwen sirve para:
- Fijar el **estilo de respuesta** (resumen → normas aplicables citadas → pasos concretos →
  aviso legal) sin depender de que el prompt lo repita cada vez.
- Reforzar el **rechazo de casos fuera de dominio** (reto extra E5) con ejemplos negativos.
- Reducir alucinación de artículos/leyes inexistentes, premiando "no lo sé, consulta el
  corpus" cuando no hay evidencia recuperada.

El modelo fine-tuneado **sigue usando RAG en inferencia** (recibe los chunks recuperados en
el prompt); el fine-tuning no reemplaza la recuperación, la complementa.

## Estructura

```
ML/
  data/
    corpus/               -> (opcional) copia de trabajo de /corpus en la raíz del repo,
                              usada solo para generar el dataset de entrenamiento/eval.
                              La copia "viva" que usa el backend en producción es la carpeta
                              /corpus de la raíz del repositorio.
    gold_cases/
      gold_cases.jsonl        Casos dorados dentro de dominio (para SFT y para E4)
      adversarial_cases.jsonl Casos fuera de dominio / adversariales (para E5 y SFT negativo)
    sft/
      train.jsonl / val.jsonl  Generados por 02_build_sft_dataset.py
  scripts/
    common.py                 Helpers compartidos (paths, lectura jsonl)
    01_prepare_corpus.py       Trocea /corpus en chunks por artículo (mismo chunker que usa
                                el backend, para mantener consistencia)
    02_build_sft_dataset.py    Construye el dataset de instrucción a partir de gold_cases +
                                adversarial_cases + chunks del corpus
    03_train_qwen_lora.py      Fine-tuning LoRA/QLoRA de Qwen2.5-Instruct con TRL
    04_merge_and_export.py     Fusiona el adaptador LoRA y exporta a GGUF para servir con
                                Ollama (despliegue 100% local, sin llaves de API)
    05_evaluate.py             Corre gold_cases + adversarial_cases contra un modelo servido
                                (Ollama o HF) y genera un reporte de aciertos
  models/                      Salidas de entrenamiento (pesos, adaptadores, GGUF) - en
                                .gitignore, no se versiona
  eval/                        Reportes de evaluación generados por 05_evaluate.py
```

## Modelo base recomendado

`Qwen2.5-1.5B-Instruct` (o `Qwen2.5-3B-Instruct` si hay GPU con >=8GB VRAM). Son lo bastante
livianos para fine-tunear en unas horas con LoRA en una GPU de consumo o en Google Colab
gratuito, y para correr cuantizados (GGUF, Q4_K_M) con buena velocidad en CPU vía Ollama
durante la demo — clave para R7 (demo en vivo) y el reto extra E3 (arranque con un solo
comando, sin depender de internet ni de llaves de API).

## Flujo de trabajo

```bash
cd ML
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 1. Preparar chunks del corpus (debe existir /corpus en la raíz del repo)
python scripts/01_prepare_corpus.py

# 2. Construir dataset de instrucción (SFT) a partir de los casos dorados/adversariales
python scripts/02_build_sft_dataset.py

# 3. Fine-tuning LoRA de Qwen (requiere GPU; en CPU funciona pero es muy lento)
python scripts/03_train_qwen_lora.py --base-model Qwen/Qwen2.5-1.5B-Instruct --epochs 3

# 4. Fusionar el adaptador y exportar a GGUF para Ollama
python scripts/04_merge_and_export.py --adapter models/qwen-proyectaduria-lora --out models/gguf

# 5. Registrar el modelo en Ollama (requiere Ollama instalado y el binario/llama.cpp para
#    convertir a GGUF si 04_merge_and_export.py no lo hizo ya)
ollama create proyectaduria-qwen -f models/gguf/Modelfile

# 6. Evaluar (gold + adversarial) contra el modelo servido en Ollama
python scripts/05_evaluate.py --provider ollama --model proyectaduria-qwen
```

El backend consume el modelo final apuntando `OLLAMA_MODEL=proyectaduria-qwen` en su `.env`
(ver `backend/apps/rag/services/llm_client.py`). Si el fine-tuning no alcanza a terminar antes
del evento, el backend cae automáticamente a un modelo base de Ollama (`qwen2.5:1.5b` o
similar) o a un proveedor externo (Gemini/Groq) vía `LLM_PROVIDER`, así que el resto de la
aplicación no queda bloqueado por el entrenamiento.

## Casos dorados y adversariales

`data/gold_cases/gold_cases.jsonl` y `data/gold_cases/adversarial_cases.jsonl` sirven doble
propósito:
1. **Entrenamiento** (02_build_sft_dataset.py los convierte en ejemplos instrucción→respuesta).
2. **Evaluación** para el reto extra E4 (set de evaluación propio, mínimo 5 casos) y como base
   de la suite de pruebas automatizadas del backend (E6), que reutiliza este mismo archivo
   (ver `backend/apps/rag/management/commands/run_eval.py`).

Cada línea es un JSON con: `id`, `pregunta`, `dominio` (`true`/`false` si es dentro/fuera del
dominio elegido), `debe_citar` (lista de normas que se espera que aparezcan citadas),
`palabras_clave_esperadas` (para verificación automática superficial) y `notas`.
