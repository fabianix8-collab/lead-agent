# Lead Agent — Agente Autónomo de Gestión de Leads

![Tests](https://github.com/TU_USUARIO/lead-agent/actions/workflows/tests.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

Agente de IA con tool-calling que automatiza el flujo completo de un lead entrante:
lectura → clasificación → acción (crear contacto en CRM, agendar reunión, o escalar
a un humano cuando hay ambigüedad) — sin intervención manual en el caso feliz.

## Capturas

> _Agrega aquí una captura real de `python demo.py` corriendo, y otra de la
> tabla de `python -m eval.run_eval` con el 8/8 — guárdalas en una carpeta
> `docs/` dentro del repo y enlázalas así:_
> `![demo](docs/demo.png)` / `![eval](docs/eval.png)`
>
> Es la diferencia entre que alguien lea 190 líneas de README o entienda el
> proyecto en 10 segundos de scroll.

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

### Configurar Airtable real (CRM)

1. Crea una cuenta gratis en **airtable.com** (el free tier alcanza de sobra
   para esta demo).
2. Crea una Base nueva llamada `Leads`, con una tabla también llamada `Leads`
   (o el nombre que prefieras — lo configuras en `AIRTABLE_TABLE_NAME`).
3. En esa tabla, crea estas columnas **exactamente con estos nombres**
   (el conector las mapea por nombre exacto):
   - `Nombre` — Single line text
   - `Email` — Single line text (o Email type)
   - `Empresa` — Single line text
   - `Prioridad` — Single select, con opciones: `caliente`, `tibio`, `frio`
   - `Notas` — Long text
4. Genera un **Personal Access Token** en airtable.com/create/tokens con
   permiso `data.records:write` sobre esa base — esa es tu `AIRTABLE_API_KEY`.
5. El `AIRTABLE_BASE_ID` lo encuentras en la URL de tu base (empieza con `app...`)
   o en la documentación de la API de tu base (Help → API documentation).
6. Completa esos 3 valores en tu `.env` y corre con `MODE=real`.

### Resto de conectores (Gmail, Calendar, Slack)

Siguen en modo mock por ahora — sus implementaciones reales están comentadas
en `connectors/` como referencia, para cuando quieras activarlas siguiendo el
mismo patrón que Airtable.

1. Completa `.env` a partir de `.env.example`.
2. `MODE=real python agent.py` — corre en loop sobre la bandeja de entrada real.

## Métricas que vale la pena mostrar en la demo/entrevista

- % de leads resueltos sin intervención humana (tasa de auto-resolución)
- % de leads correctamente escalados (no falsos negativos de ambigüedad)
- Costo estimado por lead procesado (tokens de la API × precio)
- Tiempo de respuesta promedio por lead

## Manejo de errores

Las llamadas al LLM están envueltas en reintentos con backoff exponencial
(`llm/retry.py`), distinguiendo errores transitorios (rate limit, 5xx —
vale la pena reintentar) de errores permanentes (input inválido, auth —
fallar rápido). Si todos los reintentos fallan, **el lead nunca queda en
el aire**: se escala automáticamente a humano marcando el motivo como
falla técnica, no como decisión de negocio. Esto evita el fallo silencioso
más común en demos de agentes: que un error de red se trague un lead real.

## Evaluación sistemática

`eval/cases.json` contiene 8 casos con resultado esperado (clasificación
esperada, si debe escalar, si debe agendar), incluyendo casos límite:
idioma distinto (inglés), un ticket de soporte disfrazado de lead, y un
**intento de prompt injection** en el cuerpo del correo (verifica que el
agente no obedezca instrucciones inyectadas en datos de usuario).

```bash
python -m eval.run_eval
```

Esto corre el agente contra los 8 casos y reporta accuracy de
clasificación y de escalamiento — no una demo de 6 casos mirados a ojo,
sino un benchmark repetible que puedes correr cada vez que cambies el
prompt o el modelo, para saber si mejoró o empeoró.

### Historial de iteración (evidencia real, no aspiracional)

El prompt no quedó bien a la primera — y documento el proceso a propósito,
porque es más creíble y más útil en entrevista que afirmar perfección
desde el inicio:

| Ronda | Escalamiento | Clasificación | Qué falló y por qué |
|---|---|---|---|
| 1 (prompt inicial) | 6/8 (75%) | 2/4 (50%) | El agente clasificaba un ticket de soporte como lead "caliente" (sin distinguir alcance), y confundía "tibio" con "frío" por falta de criterio explícito. También reveló que el free tier tiene un límite real de 15 req/min — el fallo en ese caso fue infraestructura, no el modelo. |
| 2 (alcance + criterio explícito) | 6/8 (75%) | 4/4 (100%) | Arreglé los dos casos anteriores, pero al ampliar la definición de "frío" abrí una puerta de escape: el modelo empezó a usar "frío" para correos vacíos o con intento de manipulación (prompt injection), en vez de reconocer que ahí no había nada que clasificar. |
| 3 (regla de manipulación + límite estricto a "frío") | 8/8 (100%) | 4/4 (100%) | Regla explícita para detectar intentos de manipulación en el cuerpo del correo, y criterio más estricto: "frío" exige al menos una señal real de negocio. |

Lección que vale la pena mencionar en entrevista: ajustar un prompt para
arreglar un caso puede introducir una regresión en otro — por eso un set
de evaluación repetible no es opcional una vez que el prompt tiene más de
2-3 reglas.

## Roadmap v2

- Memoria entre conversaciones (mismo lead escribe de nuevo → contexto persistente)
- Fine-tuning del umbral de confianza con datos reales de escalamiento
- Panel de control (Streamlit) con métricas en tiempo real
- Envío de respuesta automática al lead en casos de alta confianza

## Integración continua

Cada push a `main` corre automáticamente el set de tests (`tests/`) vía
GitHub Actions — ver `.github/workflows/tests.yml`. No requiere ninguna
API key: esos tests solo ejercitan el dispatcher de tools en modo mock,
no llaman al LLM.

## Licencia

MIT — ver [LICENSE](LICENSE).

## Autor

Fabián Baeza — Ingeniería en Informática, DUOC UC.

