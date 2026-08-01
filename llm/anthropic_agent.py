"""
Implementación del agente usando Anthropic (Claude). Requiere API key paga.
Úsala si prefieres la calidad/latencia de Claude sobre la opción gratuita de
Gemini — cambia LLM_PROVIDER=anthropic en tu .env.
"""
"""
Loop del agente: recibe un lead, conversa con el modelo, ejecuta las tools
que el modelo solicite, reinyecta los resultados, y repite hasta que el
modelo termine (no pide más tool calls) o se alcance el límite de turnos.

Este loop es intencionalmente explícito (no usa un framework) para que
cada paso sea auditable y explicable.
"""
import json
from datetime import datetime, timezone

import anthropic

from config import Config
from tools import TOOLS, ejecutar_tool

_MAX_TURNOS = 6  # límite de seguridad: evita loops infinitos de tool-calling

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


class LeadAgentAnthropic:
    def __init__(self):
        Config.validate()
        self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)

    def procesar_lead(self, lead: dict) -> dict:
        mensaje_usuario = (
            f"Nuevo lead recibido:\n"
            f"Nombre: {lead.get('nombre')}\n"
            f"Email: {lead.get('email')}\n"
            f"Empresa: {lead.get('empresa') or 'no especificada'}\n"
            f"Asunto: {lead.get('asunto')}\n"
            f"Cuerpo:\n{lead.get('cuerpo')}"
        )

        messages = [{"role": "user", "content": mensaje_usuario}]
        log_ejecucion = {"lead_id": lead.get("id"), "pasos": []}

        for turno in range(_MAX_TURNOS):
            response = self.client.messages.create(
                model=Config.CLAUDE_MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason != "tool_use":
                texto_final = "".join(
                    b.text for b in response.content if b.type == "text"
                )
                log_ejecucion["resumen_final"] = texto_final
                break

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue

                resultado = ejecutar_tool(block.name, block.input)
                log_ejecucion["pasos"].append({
                    "tool": block.name,
                    "input": block.input,
                    "resultado": resultado,
                })
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                })

            messages.append({"role": "user", "content": tool_results})
        else:
            log_ejecucion["resumen_final"] = "[límite de turnos alcanzado sin resolución]"

        return log_ejecucion
