"""
Definición de las tools que el agente puede invocar, y el dispatcher que
las conecta con los conectores reales/mock.

Diseño clave: cada tool schema fuerza al modelo a producir datos ESTRUCTURADOS
y justificados (ej. "razon_clasificacion", "nivel_confianza") — no solo la acción.
Esto es lo que hace el sistema auditable: nunca ejecutamos una acción sin saber
por qué el modelo la decidió.
"""
from config import Config
from connectors.crm_airtable import AirtableConnector
from connectors.calendar_google import CalendarConnector
from connectors.slack_notify import SlackConnector

_crm = AirtableConnector(mock=Config.is_mock())
_calendar = CalendarConnector(mock=Config.is_mock())
_slack = SlackConnector(mock=Config.is_mock())


# ---------------------------------------------------------------------------
# Schemas (formato Anthropic tool-use)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "clasificar_lead",
        "description": (
            "Clasifica el lead recibido. SIEMPRE debe llamarse primero, antes de "
            "cualquier otra acción. No ejecuta ninguna acción externa, solo registra "
            "la clasificación estructurada."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "prioridad": {
                    "type": "string",
                    "enum": ["caliente", "tibio", "frio", "spam_o_invalido"],
                },
                "servicio_interes": {
                    "type": "string",
                    "description": "Producto o servicio por el que pregunta el lead.",
                },
                "nivel_confianza": {
                    "type": "number",
                    "description": "0.0 a 1.0 — qué tan seguro está el modelo de esta clasificación.",
                },
                "razon": {
                    "type": "string",
                    "description": "Justificación breve de la clasificación (1-2 frases).",
                },
            },
            "required": ["prioridad", "nivel_confianza", "razon"],
        },
    },
    {
        "name": "crear_contacto_crm",
        "description": "Crea o actualiza el contacto del lead en el CRM (Airtable).",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string"},
                "email": {"type": "string"},
                "empresa": {"type": "string"},
                "prioridad": {"type": "string"},
                "notas": {"type": "string"},
            },
            "required": ["nombre", "email", "prioridad"],
        },
    },
    {
        "name": "agendar_reunion",
        "description": (
            "Agenda una reunión en el calendario del vendedor. Solo debe usarse "
            "para leads con prioridad 'caliente' o 'tibio' y confianza >= umbral."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email_lead": {"type": "string"},
                "asunto": {"type": "string"},
                "fecha_hora_sugerida_iso": {
                    "type": "string",
                    "description": "ISO 8601. Debe ser un horario hábil dentro de las próximas 72 horas.",
                },
                "duracion_minutos": {"type": "integer", "default": 30},
            },
            "required": ["email_lead", "asunto", "fecha_hora_sugerida_iso"],
        },
    },
    {
        "name": "escalar_a_humano",
        "description": (
            "OBLIGATORIA cuando nivel_confianza < umbral configurado, o cuando el "
            "correo es ambiguo, o cuando no hay suficiente información para "
            "clasificar. Nunca se debe adivinar en su lugar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "motivo": {"type": "string"},
                "resumen_para_humano": {
                    "type": "string",
                    "description": "Resumen de 2-3 frases para que un humano decida rápido.",
                },
            },
            "required": ["motivo", "resumen_para_humano"],
        },
    },
]


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def ejecutar_tool(nombre: str, input_data: dict) -> dict:
    """Ejecuta la tool solicitada por el modelo y devuelve un resultado
    estructurado que se reinyecta al modelo como tool_result."""

    if nombre == "clasificar_lead":
        # No ejecuta acción externa; solo confirma que quedó registrada.
        return {"status": "ok", "clasificacion_registrada": input_data}

    if nombre == "crear_contacto_crm":
        return _crm.crear_contacto(**input_data)

    if nombre == "agendar_reunion":
        return _calendar.agendar(**input_data)

    if nombre == "escalar_a_humano":
        return _slack.escalar(**input_data)

    return {"status": "error", "mensaje": f"Tool desconocida: {nombre}"}
