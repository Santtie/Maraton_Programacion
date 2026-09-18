"""Configuración de los 5 tipos de solicitud de Habeas Data que la app puede generar.

Cada tipo define los campos que se piden al usuario (además de los campos comunes de
identificación) y el fundamento legal que se cita en el documento. El frontend puede pedir
GET /api/documents/tipos/ para construir el formulario dinámicamente en vez de tener los
campos hardcodeados.
"""

CAMPOS_COMUNES = [
    {"name": "nombre_completo", "label": "Nombre completo", "type": "text", "required": True},
    {
        "name": "tipo_documento_identidad",
        "label": "Tipo de documento de identidad",
        "type": "choice",
        "choices": ["Cédula de ciudadanía", "Cédula de extranjería", "Tarjeta de identidad", "Pasaporte"],
        "required": True,
    },
    {"name": "numero_documento", "label": "Número de documento", "type": "text", "required": True},
    {"name": "correo_notificacion", "label": "Correo para notificaciones", "type": "email", "required": True},
    {"name": "telefono", "label": "Teléfono de contacto", "type": "text", "required": False},
    {"name": "ciudad", "label": "Ciudad", "type": "text", "required": True},
    {
        "name": "entidad_destinataria",
        "label": "Entidad o empresa a la que se dirige (Responsable del Tratamiento)",
        "type": "text",
        "required": True,
    },
    {
        "name": "entidad_direccion_o_correo",
        "label": "Dirección o correo de la entidad (si lo conoce)",
        "type": "text",
        "required": False,
    },
    {
        "name": "hechos",
        "label": "Cuéntanos brevemente qué pasó",
        "type": "textarea",
        "required": True,
    },
]

TIPOS_HABEAS_DATA = {
    "consulta": {
        "label": "Petición de consulta o acceso",
        "descripcion": "Exige conocer toda la información personal que un banco de datos, archivo o entidad tiene sobre el titular.",
        "articulos_fundamento": [
            "Constitución Política de Colombia, 1991 - Artículo 15",
            "Ley 1581 de 2012 - Artículo 8",
            "Ley 1581 de 2012 - Artículo 14",
        ],
        "plazo_legal": "10 días hábiles desde el recibo de la solicitud (Art. 14, Ley 1581 de 2012).",
        "campos_extra": [
            {
                "name": "informacion_a_consultar",
                "label": "¿Qué información específica quieres consultar? (opcional, déjalo vacío para pedir todo)",
                "type": "textarea",
                "required": False,
            },
        ],
    },
    "actualizacion": {
        "label": "Solicitud de actualización",
        "descripcion": "Pide modificar o completar información desactualizada o incompleta.",
        "articulos_fundamento": [
            "Ley 1581 de 2012 - Artículo 8",
            "Ley 1581 de 2012 - Artículo 15",
        ],
        "plazo_legal": "15 días hábiles desde el recibo del reclamo, prorrogables 8 días hábiles más (Art. 15, Ley 1581 de 2012).",
        "campos_extra": [
            {"name": "dato_desactualizado", "label": "¿Qué dato está desactualizado o incompleto?", "type": "textarea", "required": True},
            {"name": "informacion_correcta", "label": "¿Cuál es la información correcta y actual?", "type": "textarea", "required": True},
        ],
    },
    "rectificacion": {
        "label": "Solicitud de rectificación",
        "descripcion": "Pide corregir datos falsos, inexactos o parciales.",
        "articulos_fundamento": [
            "Ley 1581 de 2012 - Artículo 8",
            "Ley 1581 de 2012 - Artículo 15",
        ],
        "plazo_legal": "15 días hábiles desde el recibo del reclamo, prorrogables 8 días hábiles más (Art. 15, Ley 1581 de 2012).",
        "campos_extra": [
            {"name": "dato_incorrecto", "label": "¿Qué dato es falso, inexacto o parcial?", "type": "textarea", "required": True},
            {"name": "informacion_correcta", "label": "¿Cuál es la información correcta?", "type": "textarea", "required": True},
            {"name": "razon", "label": "¿Por qué consideras que el dato es incorrecto?", "type": "textarea", "required": True},
        ],
    },
    "supresion": {
        "label": "Solicitud de supresión o eliminación",
        "descripcion": "Exige el borrado de datos personales cuando caducó el tiempo legal de reporte o el tratamiento incumple los principios legales.",
        "articulos_fundamento": [
            "Ley 1581 de 2012 - Artículo 8",
            "Ley 1581 de 2012 - Artículo 15",
        ],
        "plazo_legal": "15 días hábiles desde el recibo del reclamo, prorrogables 8 días hábiles más (Art. 15, Ley 1581 de 2012).",
        "campos_extra": [
            {"name": "dato_a_suprimir", "label": "¿Qué dato específico quieres que eliminen?", "type": "textarea", "required": True},
            {
                "name": "razon_supresion",
                "label": "¿Por qué debe eliminarse? (ej. venció el tiempo legal de reporte, ya no es necesario, tratamiento indebido)",
                "type": "textarea",
                "required": True,
            },
        ],
    },
    "revocatoria": {
        "label": "Revocatoria de la autorización",
        "descripcion": "Cancela el permiso otorgado previamente para el tratamiento de los datos o su uso comercial.",
        "articulos_fundamento": [
            "Ley 1581 de 2012 - Artículo 8",
            "Ley 1581 de 2012 - Artículo 9",
        ],
        "plazo_legal": "La revocatoria puede solicitarse en cualquier momento (Art. 8 lit. e, Ley 1581 de 2012).",
        "campos_extra": [
            {
                "name": "finalidad_a_revocar",
                "label": "¿Para qué finalidad habías autorizado el uso de tus datos?",
                "type": "textarea",
                "required": True,
            },
            {"name": "fecha_autorizacion", "label": "Fecha aproximada en que diste la autorización (si la recuerdas)", "type": "text", "required": False},
        ],
    },
}


def get_tipo_config(tipo: str) -> dict:
    if tipo not in TIPOS_HABEAS_DATA:
        raise KeyError(tipo)
    return TIPOS_HABEAS_DATA[tipo]


def get_campos_requeridos(tipo: str) -> list[dict]:
    return CAMPOS_COMUNES + TIPOS_HABEAS_DATA[tipo]["campos_extra"]


def serialize_tipos_for_frontend() -> dict:
    return {
        "campos_comunes": CAMPOS_COMUNES,
        "tipos": {
            key: {
                "label": cfg["label"],
                "descripcion": cfg["descripcion"],
                "plazo_legal": cfg["plazo_legal"],
                "articulos_fundamento": cfg["articulos_fundamento"],
                "campos_extra": cfg["campos_extra"],
            }
            for key, cfg in TIPOS_HABEAS_DATA.items()
        },
    }
