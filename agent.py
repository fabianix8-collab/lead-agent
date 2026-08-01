"""
Factory del agente: elige la implementación según LLM_PROVIDER (config.py).
El resto del proyecto (demo.py, tests) importa LeadAgent desde aquí y no
necesita saber si por debajo corre Gemini o Claude.

Por qué este patrón: te permite cambiar de proveedor con una variable de
entorno, sin tocar tools.py, conectores, ni el código que llama al agente.
Es la aplicación práctica de "programar contra una interfaz, no una
implementación" en un proyecto chico donde no vale la pena una capa de
abstracción más pesada.
"""
from config import Config


def LeadAgent():
    if Config.LLM_PROVIDER == "gemini":
        from llm.gemini_agent import LeadAgentGemini
        return LeadAgentGemini()

    if Config.LLM_PROVIDER == "anthropic":
        from llm.anthropic_agent import LeadAgentAnthropic
        return LeadAgentAnthropic()

    raise ValueError(
        f"LLM_PROVIDER desconocido: '{Config.LLM_PROVIDER}'. Usa 'gemini' o 'anthropic'."
    )
