# Corpus normativo — ProyectadurIA

Este corpus alimenta la arquitectura RAG del backend (`backend/apps/rag`). El dominio del
proyecto es **Derechos Fundamentales, Protección de Datos e Intimidad** (debido proceso,
libertad de expresión e información, igualdad, libre desarrollo de la personalidad y
Habeas Data), con foco práctico en las cinco solicitudes de Habeas Data (consulta,
actualización, rectificación, supresión, revocatoria).

## Estado actual

Los archivos `.txt` de este directorio son una **semilla real pero parcial**: el texto fue
obtenido de fuentes oficiales/semioficiales (Secretaría del Senado, Alcaldía de Bogotá –
Régimen Legal, Función Pública) el 2026-09-18, pero **no todos los artículos están
transcritos de forma 100% literal e íntegra** (algunos fragmentos fueron resumidos por la
herramienta de extracción). Cada archivo indica su `ESTADO` en el encabezado.

**Antes del evento, el equipo debe:**
1. Verificar cada artículo contra el texto oficial (enlaces en el encabezado de cada archivo).
2. Completar los artículos marcados como `[RESUMEN - completar con texto literal]`.
3. Reemplazar esta carpeta con la que entregue la organización el día del evento (sección 9
   del enunciado: kit de arranque con `/corpus` de 10-15 documentos ya descargados), fusionando
   ambos conjuntos si aplica.
4. Añadir 2-4 sentencias de la Corte Constitucional (carpeta `jurisprudencia/`) para reforzar
   E1 (RAG con corpus propio) y E2 (citas verificables).

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
