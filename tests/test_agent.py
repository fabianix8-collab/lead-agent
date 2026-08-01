"""
Tests básicos, corren sin API key (no tocan el LLM, solo el dispatcher
de tools en modo mock). Para probar el loop completo del agente hace
falta ANTHROPIC_API_KEY — eso se prueba manualmente vía demo.py.

Correr con: pytest tests/
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools import ejecutar_tool


def test_clasificar_lead_no_ejecuta_accion_externa():
    resultado = ejecutar_tool("clasificar_lead", {
        "prioridad": "caliente",
        "nivel_confianza": 0.9,
        "razon": "test",
    })
    assert resultado["status"] == "ok"


def test_crear_contacto_crm_modo_mock():
    resultado = ejecutar_tool("crear_contacto_crm", {
        "nombre": "Test Lead",
        "email": "test@example.com",
        "prioridad": "tibio",
    })
    assert resultado["status"] == "ok"
    assert resultado["modo"] == "mock"
    assert "record_id" in resultado


def test_agendar_reunion_fecha_invalida():
    resultado = ejecutar_tool("agendar_reunion", {
        "email_lead": "test@example.com",
        "asunto": "Reunión de prueba",
        "fecha_hora_sugerida_iso": "no-es-una-fecha",
    })
    assert resultado["status"] == "error"


def test_escalar_a_humano_modo_mock():
    resultado = ejecutar_tool("escalar_a_humano", {
        "motivo": "correo ambiguo",
        "resumen_para_humano": "test de escalamiento",
    })
    assert resultado["status"] == "ok"


def test_tool_desconocida():
    resultado = ejecutar_tool("tool_que_no_existe", {})
    assert resultado["status"] == "error"
