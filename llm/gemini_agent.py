"""
Implementación del agente usando Google Gemini (free tier — sin costo, sin
tarjeta de crédito). Misma lógica de negocio que llm/anthropic_agent.py:
clasificar → decidir tool(s) → ejecutar → reinyectar resultado → repetir.

La diferencia es solo de "cableado" con la API: Gemini usa su propio
formato de function declarations y de function_response. El SYSTEM_PROMPT
y el criterio de decisión son los mismos que en la versión de Anthropic,
para que el comportamiento del agente no cambie según el proveedor.
"""
from datetime import datetime, timezone

from google import genai
from google.genai import types

from config import Config
from tools import TOOLS, ejecutar_tool

_MAX_TURNOS = 6

SYSTEM_PROMPT = f"""Eres un agente de gestión de leads para un equipo de ventas B2B.

Tu trabajo, para cada lead recibido, es:
1. Llamar SIEMPRE primero a `clasificar_lead` con tu evaluación honesta.
2. Si nivel_confianza < {Config.CONFIDENCE_THRESHOLD} O el correo es spam/ambiguo/
   sin información suficiente: llama a `escalar_a_humano` y DETENTE. No inventes
   ni asumas datos que no están en el correo.
3. Si el lead es claro y prioridad es "caliente" o "tibio" con confianza suficiente:
   llama a `crear_contacto_crm` y, si el lead pide o amerita una reunión, también
   a `agendar_reunion` (usa un horario hábil dentro de las próximas 72 horas,
   asume que hoy es {datetime.now(timezone.utc).strftime('%Y-%m-%d')}).
4. Si prioridad es "frio": solo llama a `crear_contacto_crm`, sin agendar reunión.
5. Nunca declares en texto que ejecutaste una acción sin haber llamado la tool
   correspondiente. Nunca asumas datos de contacto o de negocio que no estén
   explícitos en el correo.

Sé conciso. Cuando termines de procesar el lead, responde con un resumen breve
en texto plano (sin más tool calls) explicando qué decidiste y por qué.
"""


def _tools_a_formato_gemini() -> list[types.Tool]:
    """Convierte los schemas de tools.py (formato Anthropic) al formato que
    espera Gemini. Ambos usan JSON Schema por debajo, así que el mapeo es
    casi directo: input_schema -> parameters."""
    declaraciones = [
        types.FunctionDeclaration(
            name=t["name"],
            description=t["description"],
            parameters=t["input_schema"],
        )
        for t in TOOLS
    ]
    return [types.Tool(function_declarations=declaraciones)]


class LeadAgentGemini:
    def __init__(self):
        Config.validate()
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.tools = _tools_a_formato_gemini()

    def procesar_lead(self, lead: dict) -> dict:
        mensaje_usuario = (
            f"Nuevo lead recibido:\n"
            f"Nombre: {lead.get('nombre')}\n"
            f"Email: {lead.get('email')}\n"
            f"Empresa: {lead.get('empresa') or 'no especificada'}\n"
            f"Asunto: {lead.get('asunto')}\n"
            f"Cuerpo:\n{lead.get('cuerpo')}"
        )

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=mensaje_usuario)])]
        log_ejecucion = {"lead_id": lead.get("id"), "pasos": []}

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=self.tools,
        )

        for _turno in range(_MAX_TURNOS):
            response = self.client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=contents,
                config=config,
            )

            candidato = response.candidates[0]
            contents.append(candidato.content)

            function_calls = [
                p.function_call for p in candidato.content.parts if p.function_call
            ]

            if not function_calls:
                texto_final = "".join(
                    p.text for p in candidato.content.parts if p.text
                )
                log_ejecucion["resumen_final"] = texto_final
                break

            partes_resultado = []
            for fc in function_calls:
                resultado = ejecutar_tool(fc.name, dict(fc.args))
                log_ejecucion["pasos"].append({
                    "tool": fc.name,
                    "input": dict(fc.args),
                    "resultado": resultado,
                })
                partes_resultado.append(
                    types.Part.from_function_response(name=fc.name, response=resultado)
                )

            contents.append(types.Content(role="user", parts=partes_resultado))
        else:
            log_ejecucion["resumen_final"] = "[límite de turnos alcanzado sin resolución]"

        return log_ejecucion
