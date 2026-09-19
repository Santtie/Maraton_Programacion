# ProyectadurIA

Asesor legal de bolsillo para **Derechos Fundamentales, Protección de Datos e Intimidad**
(debido proceso, libertad de expresión e información, igualdad ante la ley, libre desarrollo
de la personalidad y Habeas Data), construido para el reto "Asesor Legal de Bolsillo" del
maratón de programación.

> **Equipo:** _completar el día del evento_ (nombre del equipo e integrantes).

## El problema y la solución

Una persona sin recursos para pagar un abogado no sabe si su situación tiene respaldo legal
ni qué pasos seguir. ProyectadurIA permite:

1. **Chat de consulta**: el usuario describe su caso en lenguaje natural y recibe un resumen
   legal, la norma aplicable citada (con enlace/fragmento fuente), pasos concretos a seguir y
   el aviso legal obligatorio — usando una arquitectura RAG sobre un corpus normativo real
   (`/corpus`) y un modelo Qwen fine-tuneado (`/ML`). Si la consulta no pertenece al dominio
   elegido, lo declara en vez de inventar una respuesta.
2. **Generador de solicitudes de Habeas Data**: a partir de un formulario dinámico, genera el
   texto y el PDF de los 5 tipos de solicitud de la Ley 1581 de 2012 — consulta/acceso,
   actualización, rectificación, supresión y revocatoria de la autorización —, citando el
   fundamento legal exacto.

## Arquitectura

```
maraton/
  corpus/       Corpus normativo real (Constitución, Ley 1581/2012, Decreto 1377/2013...)
                usado tanto por el RAG del backend como por el entrenamiento/evaluación en ML/
  backend/      Django REST: auth (JWT), chat RAG, generador de documentos, arquitectura RAG
                completa (embeddings, ChromaDB, guardián de dominio, cliente LLM)
  frontend/     Vue 3 + TS: login/registro, menú, chat, formulario de Habeas Data
  ML/           Entrenamiento del Qwen fine-tuneado (LoRA) + casos dorados/adversariales +
                evaluación. Independiente de backend/frontend.
  docker-compose.yml   Arranque del backend con un solo comando (reto extra E3)
```

Detalle técnico de cada parte en su propio README: [`backend/README.md`](backend/README.md)
(incluye diagrama de flujo de una consulta), [`frontend/README.md`](frontend/README.md),
[`ML/README.md`](ML/README.md), [`corpus/README.md`](corpus/README.md).

## Requisitos

- Python 3.12+
- Node.js 22+ (o 24+) y npm
- Para el chat con IA: **una** de estas opciones (sin ninguna, el resto de la app funciona
  igual, pero el chat responde con un error controlado):
  - [Ollama](https://ollama.com) con el modelo `proyectaduria-qwen` entrenado en `/ML`
    registrado (ver `ML/README.md`), **o**
  - el modelo fusionado de `/ML` servido directo con `transformers` (`LLM_PROVIDER=local_hf`
    en `backend/.env`, requiere GPU NVIDIA para que sea razonablemente rápido), **o**
  - una API key gratuita de [Google AI Studio](https://aistudio.google.com) (Gemini) o
    [Groq](https://console.groq.com)

## Puesta en marcha (Windows)

### 1. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
# Editar .env: como mínimo revisar LLM_PROVIDER (ver sección "Requisitos" arriba)

python manage.py migrate
python manage.py createsuperuser        # opcional, para /admin/

python manage.py ingest_corpus --reset  # indexa /corpus en ChromaDB (RAG)

python manage.py runserver
```

El backend queda en `http://localhost:8000/`.

### 2. Frontend (en otra terminal)

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

El frontend queda en `http://localhost:5173/`. Entrá, creá una cuenta desde "Regístrate"
(nombre, usuario, contraseña) y probá el menú principal.

### 3. (Opcional) Entrenar/registrar el modelo

Ver [`ML/README.md`](ML/README.md) para el flujo completo: preparar el corpus, construir el
dataset de instrucción, fine-tunear Qwen con LoRA, fusionar y exportar, y evaluar. El chat
funciona sin esto (cae a Gemini/Groq si se configura una API key en `backend/.env`), pero el
modelo fine-tuneado es lo que da el estilo de respuesta esperado y el reforzamiento del
rechazo de consultas fuera de dominio.

## Puesta en marcha (Linux / macOS)

Igual que arriba, cambiando `python -m venv .venv` → `python3 -m venv .venv`,
`.venv\Scripts\activate` → `source .venv/bin/activate`, y `copy` → `cp`.

## Con Docker (un solo comando)

```bash
cd backend && cp .env.example .env   # ajustar valores
cd ..
docker compose up
```

Levanta el backend en `http://localhost:8000/` (migraciones + indexado del corpus +
servidor, todo en el arranque). El frontend por ahora se sigue corriendo aparte con
`npm run dev` (ver `frontend/README.md`).

## Variables de entorno

Ver `backend/.env.example` y `frontend/.env.example` para la lista completa comentada. Las
más relevantes:

| Variable | Dónde | Para qué |
|---|---|---|
| `LLM_PROVIDER` | backend | `ollama` \| `local_hf` \| `gemini` \| `groq` — quién genera las respuestas del chat |
| `OLLAMA_MODEL` | backend | nombre del modelo registrado en Ollama (`proyectaduria-qwen`) |
| `LOCAL_HF_MODEL_PATH` | backend | carpeta del modelo fusionado, si `LLM_PROVIDER=local_hf` |
| `GEMINI_API_KEY` / `GROQ_API_KEY` | backend | llaves de respaldo con capa gratuita (dejar vacío si no se usan) |
| `RAG_CORPUS_DIR` | backend | dónde está `/corpus` (por defecto `../corpus`) |
| `VITE_API_BASE_URL` | frontend | URL del backend (por defecto `http://localhost:8000`) |

Ninguna llave real va en el repositorio: cada `.env` está en `.gitignore`, solo se versiona el
`.env.example` correspondiente.

## Flujo de uso

1. Registro/login (`/registro`, `/login`).
2. Menú principal: elegir "Realizar una consulta" o "Generar una petición de Habeas Data".
3. **Consulta**: escribir el caso en lenguaje natural → respuesta con resumen, norma citada,
   pasos y aviso legal.
4. **Petición**: elegir uno de los 5 tipos → completar el formulario → descargar el PDF
   generado.

## Retos extra implementados

- **E1** RAG con corpus propio (`/corpus`, indexado en ChromaDB).
- **E2** Citas verificables (norma + artículo + fragmento fuente + URL en cada respuesta).
- **E3** Arranque con un solo comando (`docker compose up` para el backend).
- **E4** Set de evaluación propio (`ML/data/gold_cases/`, 100 casos; `python manage.py run_eval`).
- **E5** Manejo de casos fuera de dominio (guardián de ruido + el LLM declara el rechazo con
  un texto exacto detectable, ver `backend/apps/rag/services/domain_guard.py`).
- **E6** Pruebas automatizadas (`python manage.py test`, corren offline sin depender de un LLM).
- **E7** Generación de documento (texto + PDF de las solicitudes de Habeas Data).
- **E9** Respuestas en streaming (`/api/chat/stream/`, Server-Sent Events).
- **E10** Historial persistente (conversaciones y documentos guardados en base de datos).
- **E11** Documentación técnica ampliada (diagrama de arquitectura en `backend/README.md`).
- **E12** Instrucciones verificadas para Windows y Linux/macOS (arriba).

Pendientes: E8 (voz) y E13 (accesibilidad) no están implementados todavía.
