# Lead Agent — Agente Autónomo de Gestión de Leads

Agente de IA con tool-calling que automatiza el flujo completo de un lead entrante:
lectura → clasificación → acción (crear contacto en CRM, agendar reunión, o escalar
a un humano cuando hay ambigüedad) — sin intervención manual en el caso feliz.

## Por qué este proyecto (y no un chatbot más)

La mayoría de los proyectos de portafolio con LLM son chatbots que *responden preguntas*.
Este agente *ejecuta acciones con consecuencias reales* sobre sistemas externos (CRM,
calendario, notificaciones). Esa es la diferencia entre "demo de IA" y "automatización
de negocio", que es exactamente lo que el mercado de automatización está pidiendo en 2026.

## Arquitectura

```
 correo/formulario entrante
          │
          ▼
   ┌─────────────┐      tool-calling loop      ┌──────────────────┐
   │   Ingesta    │ ───────────────────────────▶│   Claude (LLM)   │
   └─────────────┘                              └────────┬─────────┘
                                                           │ decide qué tool(s) llamar
                                    ┌──────────────────────┼──────────────────────┐
                                    ▼                       ▼                      ▼
                          crear_contacto_crm       agendar_reunion        escalar_a_humano
                                    │                       │                      │
                                    ▼                       ▼                      ▼
                            Airtable/CRM            Google Calendar             Slack
```

Cada conector implementa una interfaz común con dos modos:
- **mock**: simula la acción, guarda el resultado en memoria/JSON local. No requiere
  credenciales. Es el modo por defecto — así el proyecto se puede demostrar y probar
  de inmediato.
- **real**: llama a la API real (Gmail, Airtable, Google Calendar, Slack). Requiere
  credenciales en `.env` (ver `.env.example`).

Cambiar de modo es una sola variable de entorno (`MODE=mock` o `MODE=real`) — el
agente y el LLM no saben ni les importa en qué modo están corriendo los conectores.

## Decisiones de diseño (para poder defenderlas en entrevista)

1. **Tool-calling nativo, sin framework de agentes.** Con 4-5 tools bien definidas,
   un loop manual da control total y es más fácil de explicar que una capa de
   abstracción tipo LangChain que oculta el "por qué" de cada decisión.
2. **El LLM nunca "narra" una acción sin ejecutarla.** Toda acción de compromiso pasa
   por una tool real con su propio resultado verificable. Evita el fallo clásico de
   demos de agentes: que el modelo diga que hizo algo sin haberlo hecho.
3. **Umbral de confianza obligatorio.** La tool `escalar_a_humano` no es opcional en
   el prompt — el sistema exige que el agente la use cuando la clasificación no es
   clara, en vez de adivinar. Esto es lo que separa un "happy path" de un sistema
   production-ready.
4. **Trazabilidad completa.** Cada ejecución genera un log estructurado (JSON) con:
   input recibido, razonamiento del modelo, tools invocadas, resultado de cada una,
   y decisión final. Esto es lo que le muestras a un cliente/evaluador para probar
   que el sistema es auditable, no una caja negra.

## Estructura del proyecto

```
lead-agent/
├── agent.py                 # loop principal de tool-calling
├── tools.py                 # definición de schemas + dispatcher de tools
├── config.py                # configuración, modo mock/real
├── connectors/
│   ├── crm_airtable.py
│   ├── calendar_google.py
│   ├── gmail_client.py
│   └── slack_notify.py
├── mock_data/
│   └── sample_leads.json    # 6 leads de ejemplo (casos variados)
├── demo.py                  # corre el agente sobre los leads de ejemplo
├── tests/
│   └── test_agent.py
├── requirements.txt
└── .env.example
```

## Cómo correrlo (100% gratis, sin tarjeta de crédito)

Por defecto el proyecto usa **Google Gemini** (modelo `gemini-flash-lite-latest`),
free tier real de Google: sin tarjeta, sin vencimiento, con function calling
incluido. También soporta Anthropic (Claude) como alternativa paga — se elige
con la variable `LLM_PROVIDER` en `.env`.

```bash
pip install -r requirements.txt
cp .env.example .env
# genera tu key gratis en https://aistudio.google.com/apikey y pégala en .env
python demo.py
```

Nota honesta sobre el free tier de Gemini: Google puede usar tus inputs/outputs
para mejorar sus modelos mientras uses la capa gratuita. Para una demo de
portafolio no es problema; con datos reales de clientes lo correcto sería
pasar a un tier pago con privacidad de datos.

Esto procesa los 6 leads de `mock_data/sample_leads.json` (casos: lead caliente
claro, lead frío, correo ambiguo/spam, lead que pide reunión urgente, lead
duplicado, y correo sin información suficiente) y muestra en consola la decisión
del agente para cada uno, con el log de tools invocadas.

## Cómo pasar a modo real

1. Completa `.env` a partir de `.env.example` (credenciales de Gmail API, Airtable,
   Google Calendar, Slack).
2. `MODE=real python agent.py` — corre en loop sobre la bandeja de entrada real.

## Métricas que vale la pena mostrar en la demo/entrevista

- % de leads resueltos sin intervención humana (tasa de auto-resolución)
- % de leads correctamente escalados (no falsos negativos de ambigüedad)
- Costo estimado por lead procesado (tokens de la API × precio)
- Tiempo de respuesta promedio por lead

## Roadmap v2 (para mencionar como "próximos pasos" en la entrevista)

- Memoria entre conversaciones (mismo lead escribe de nuevo → contexto persistente)
- Fine-tuning del umbral de confianza con datos reales de escalamiento
- Panel de control (Streamlit) con métricas en tiempo real
- Envío de respuesta automática al lead en casos de alta confianza
