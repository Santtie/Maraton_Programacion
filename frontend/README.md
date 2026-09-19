# ProyectadurIA — Frontend (Vue 3 + Vite)

Interfaz de ProyectadurIA: login/registro, menú principal, chat RAG y generador de
solicitudes de Habeas Data. Consume la API del backend en `../backend` (Django REST).

## Puesta en marcha

```sh
npm install
cp .env.example .env       # ajustar VITE_API_BASE_URL si el backend no corre en localhost:8000
npm run dev
```

Requiere el backend corriendo (`http://localhost:8000` por defecto) con CORS habilitado
para `http://localhost:5173` (ya configurado por defecto en `backend/.env.example`).

## Estructura

```
src/
  api/          Cliente fetch + JWT (client.ts) y funciones por dominio: auth, chat, documents
  stores/       auth.ts (Pinia): sesión, tokens y usuario, persistidos en localStorage
  router/       Rutas + guard de autenticación (redirige a /login si no hay sesión)
  views/
    LoginView.vue / SignupView.vue        Autenticación
    MainMenuView.vue                      "¿Qué deseas hacer?"
    ChatView.vue                          Chat RAG (POST /api/chat/message/)
    PeticionTiposView.vue                 Selección de tipo de Habeas Data (GET /api/documents/tipos/)
    PeticionFormView.vue                  Formulario dinámico + generación + descarga de PDF
  utils/formatMessage.ts                  Formateo seguro (escapa HTML) de la respuesta del chat
```

La paleta de color ("Dusk": `#F0D06B`, `#D95A40`, `#BF2742`, `#501E31`, `#577C80`,
`#FFFDF7`) está definida como variables CSS en `src/assets/base.css`.

## Notas

- El chat requiere que el backend tenga un proveedor de LLM disponible (Ollama corriendo, o
  `GEMINI_API_KEY`/`GROQ_API_KEY` configurada) — ver `backend/README.md`. Sin eso, el envío de
  mensajes falla con un error controlado en la UI (no rompe la aplicación).
- La generación de documentos de Habeas Data **no** depende del LLM (es basada en plantillas
  + el corpus normativo), así que funciona aunque el chat todavía no tenga modelo servido.
- La descarga de PDF se hace autenticada (fetch + Blob), no con un enlace directo, porque el
  documento contiene datos personales del usuario.

## Otros comandos

```sh
npm run build       # type-check + build de producción
npm run test:unit    # Vitest
npm run lint         # ESLint + oxlint
```
