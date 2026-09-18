# Corpus normativo — ProyectadurIA

Este corpus alimenta la arquitectura RAG del backend (`backend/apps/rag`). El dominio del
proyecto es **Derechos Fundamentales, Protección de Datos e Intimidad** (debido proceso,
libertad de expresión e información, igualdad, libre desarrollo de la personalidad y
Habeas Data), con foco práctico en las cinco solicitudes de Habeas Data (consulta,
actualización, rectificación, supresión, revocatoria).

## Estado actual (2026-09-18)

- `constitucion/constitucion_politica_1991_derechos_fundamentales.txt` — **verificado**.
  Artículos 13, 15, 16, 20, 23, 29 y 74 con texto literal completo, contrastado contra
  Alcaldía de Bogotá – Régimen Legal (`alcaldiabogota.gov.co/sisjur`).
- `leyes/ley_1581_2012_proteccion_datos.txt` — **verificado**. Artículos 1, 3, 4 (los 8
  literales), 8, 9, 14, 15 y 16 con texto literal completo.
- `leyes/decreto_1377_2013_reglamentario.txt` — **verificado**. Artículos 5, 21 y 23 con texto
  literal completo (cubre solo una parte del decreto; se puede ampliar).
- `leyes/ley_1266_2008_habeas_data_financiero.txt` — **pendiente**. No se encontró una fuente
  con texto literal accesible (secretariasenado.gov.co no respondió; la página de Alcaldía de
  Bogotá carga el articulado por JavaScript). El archivo documenta el intento y las fuentes
  recomendadas a seguir. **No citar este archivo en producción hasta verificarlo.**
- `jurisprudencia/` — vacío, ver su propio README.

**Antes del evento, el equipo debe:**
1. Completar `ley_1266_2008_habeas_data_financiero.txt` con texto literal (ver notas de
   intento dentro del archivo) — relevante para el caso de supresión por caducidad del reporte
   en centrales de riesgo.
2. Añadir 2-4 sentencias de la Corte Constitucional (carpeta `jurisprudencia/`) para reforzar
   E1 (RAG con corpus propio) y E2 (citas verificables).
3. Re-ejecutar `python manage.py ingest_corpus --reset` (backend) cada vez que se edite algo
   aquí, para reindexar la base vectorial.
4. Si la organización entrega su propio kit con `/corpus` el día del evento (sección 9 del
   enunciado), fusionarlo con esta carpeta en vez de reemplazarla.

## Formato esperado por el ingestor (`ML/scripts/01_prepare_corpus.py` y
`backend/apps/rag/management/commands/ingest_corpus.py`)

Cada archivo `.txt` debe tener un encabezado de metadatos y luego artículos separados por
`### Artículo N`:

```
FUENTE: <nombre humano de la norma>
NORMA: <identificador corto, ej. "Ley 1581 de 2012">
URL: <enlace fuente>
FECHA_CONSULTA: <YYYY-MM-DD>
ESTADO: <verificado | seed parcial | pendiente>

### Artículo 1
Texto del artículo...

### Artículo 2
Texto del artículo...
```

El ingestor trocea (chunk) por artículo, adjunta la metadata a cada chunk y lo indexa en la
base vectorial. Cada respuesta del asistente puede así citar `NORMA + Artículo N` con enlace
(`URL`), cumpliendo E2 (citas verificables).

## Añadir un documento nuevo

1. Crear un `.txt` con el formato anterior en la subcarpeta correspondiente
   (`constitucion/`, `leyes/`, `jurisprudencia/`).
2. Ejecutar `python manage.py ingest_corpus` desde `backend/` (o el script equivalente en
   `ML/scripts/01_prepare_corpus.py` si se está preparando el dataset de entrenamiento/eval).
