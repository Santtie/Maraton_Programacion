# ProyectadurIA — Backend (Django REST)

Backend de ProyectadurIA: autenticación, chat con arquitectura RAG y generador de
solicitudes de Habeas Data. Dominio: **Derechos Fundamentales, Protección de Datos e
Intimidad** (debido proceso, libertad de expresión e información, igualdad, libre desarrollo
de la personalidad y Habeas Data).

> Nota: este README técnico documenta cómo correr el backend. El README.md raíz del
> repositorio (con nombre del equipo, integrantes, capturas, etc. — requerido por el
> enunciado del maratón) se completa el día del evento.

## Estructura

```
backend/
  config/                 settings, urls, wsgi/asgi
  apps/
    accounts/              signup / login (JWT) / usuario actual
    chat/                  conversaciones, mensajes, endpoints de chat (normal y streaming)
    documents/              generador de solicitudes de Habeas Data (texto + PDF)
    rag/                    arquitectura RAG: embeddings, ChromaDB, retriever, guardián de
                             dominio, cliente LLM (Ollama/Gemini/Groq), pipeline, comandos de
                             ingesta y evaluación
```

La arquitectura RAG vive en `apps/rag` y es usada tanto por `apps/chat` (para responder
preguntas) como por `apps/documents` (para citar el fundamento legal exacto en los documentos
generados).

## Arquitectura (flujo de una consulta de chat)

```
Usuario (frontend)
   │  POST /api/chat/message/ o /stream/  {query}
   ▼
apps/chat.views.ChatMessageView / ChatStreamView
   │  guarda turno de usuario, delega en:
   ▼
apps/rag.services.pipeline.RAGPipeline
   │
   ├─ 1) Retriever ─────────────► embeddings.py (sentence-transformers / Gemini)
   │        │                          │
   │        ▼                          ▼
   │   vectorstore.py (ChromaDB, persistente en /backend/chroma_db)
   │        ▲
   │        │  indexado por: manage.py ingest_corpus  <──  /corpus (.txt por artículo)
   │
   ├─ 2) domain_guard.is_in_domain(query, citas) ─► si es False: OUT_OF_DOMAIN_MESSAGE (no
   │        llama al LLM, evita alucinar y ahorra costo/latencia)
   │
   └─ 3) llm_client.CompositeLLMClient ─► Ollama (Qwen fine-tuneado, local) con caída a
            Gemini/Groq si el primario falla
   ▼
Respuesta {resumen, normas citadas + fragmento fuente, pasos, aviso legal} + citations[]
   │
   ▼
apps/chat.models (Conversation, Message) — persistido en la base de datos (historial
sobrevive al reinicio, reto extra E10)
```

`apps/documents` reutiliza `apps/rag.services.ingest.load_corpus()` para citar el mismo
fundamento legal verificable en los documentos de Habeas Data generados (texto + PDF).

## Puesta en marcha

**Windows:**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env          # y ajustar valores si aplica

python manage.py migrate
python manage.py createsuperuser   # opcional, para entrar a /admin/

# Indexar el corpus normativo (/corpus en la raíz del repo) en la base vectorial
python manage.py ingest_corpus --reset

python manage.py runserver
```

**Linux / macOS:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env

python manage.py migrate
python manage.py ingest_corpus --reset
python manage.py runserver
```

**Con Docker (un solo comando, reto extra E3)** — desde la raíz del repositorio, con
`backend/.env` ya creado:

```bash
docker compose up
```

El servidor queda en `http://localhost:8000/`. El frontend (Vite/Vue, puerto 5173 por
defecto) ya está habilitado en CORS (`CORS_ALLOWED_ORIGINS` en `.env`).

### Modelo de lenguaje (chat)

Por defecto `LLM_PROVIDER=ollama`, apuntando a `OLLAMA_MODEL=proyectaduria-qwen` (el modelo
entrenado en `/ML`). Si Ollama no está corriendo o el modelo aún no existe:

1. Instala [Ollama](https://ollama.com) y descarga un modelo base mientras entrenas el
   propio: `ollama pull qwen2.5:1.5b`, y pon `OLLAMA_MODEL=qwen2.5:1.5b` en `.env` como
   solución temporal.
2. O cambia `LLM_PROVIDER=gemini` (o `groq`) y coloca la respectiva API key en `.env` — ambos
   tienen capa gratuita (ver sección 8 del enunciado del maratón).
3. `LLM_FALLBACK_PROVIDER` se usa automáticamente si el proveedor primario falla en tiempo de
   ejecución (por ejemplo Ollama caído durante la demo).

### Evaluación (reto extra E4/E6)

```bash
python manage.py run_eval
```

Corre los casos de `ML/data/gold_cases/gold_cases.jsonl` y `adversarial_cases.jsonl` contra el
pipeline RAG real (requiere que el LLM configurado esté disponible) y deja un reporte en
`backend/eval_reports/`.

Para pruebas automatizadas que **no** dependen de red ni de un modelo corriendo (para CI o
para correr en cualquier máquina durante la demo, reto extra E6):

```bash
python manage.py test
```

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/auth/signup/` | Registro: `{nombre, username, password}` |
| POST | `/api/auth/login/` | Login JWT: `{username, password}` -> `access`, `refresh`, `user` |
| POST | `/api/auth/login/refresh/` | Refresca el access token |
| GET | `/api/auth/me/` | Usuario autenticado actual |
| POST | `/api/chat/message/` | `{query, conversation_id?}` -> respuesta RAG completa |
| POST | `/api/chat/stream/` | Igual, pero streaming SSE (reto extra E9) |
| GET | `/api/chat/conversations/` | Historial de conversaciones (reto extra E10) |
| GET/DELETE | `/api/chat/conversations/<id>/` | Detalle / borrado de una conversación |
| GET | `/api/documents/tipos/` | Configuración de los 5 tipos de Habeas Data (para el form) |
| POST | `/api/documents/generate/` | `{tipo, campos}` -> genera texto + PDF |
| GET | `/api/documents/` | Historial de documentos generados por el usuario |
| GET | `/api/documents/<id>/pdf/` | Descarga el PDF generado |

Todas las rutas excepto `signup` y `login` requieren el header `Authorization: Bearer <access>`.

## Aviso legal y límites (criterio "Responsabilidad y límites")

El pipeline RAG (`apps/rag/services/pipeline.py`) siempre:
- Declara explícitamente cuando una consulta está fuera del dominio elegido, en vez de
  inventar una respuesta (`apps/rag/services/domain_guard.py`).
- Maneja entradas vacías sin fallar ni alucinar.
- Incluye el aviso legal obligatorio al final de cada respuesta dentro de dominio.
- Nunca cita normas que no vengan respaldadas por el corpus recuperado.
