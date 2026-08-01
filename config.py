"""
Configuración central. Toda variable de entorno se lee UNA vez, aquí,
y el resto del proyecto importa desde este módulo. Evita el anti-patrón
de hacer os.getenv() esparcido por todo el código.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MODE: str = os.getenv("MODE", "mock").lower()  # "mock" | "real"

    # Proveedor de LLM: "gemini" (gratis, default) | "anthropic" (pago)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini").lower()

    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))

    # Conectores reales
    GMAIL_CREDENTIALS_PATH: str = os.getenv("GMAIL_CREDENTIALS_PATH", "")
    GOOGLE_CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    AIRTABLE_API_KEY: str = os.getenv("AIRTABLE_API_KEY", "")
    AIRTABLE_BASE_ID: str = os.getenv("AIRTABLE_BASE_ID", "")
    AIRTABLE_TABLE_NAME: str = os.getenv("AIRTABLE_TABLE_NAME", "Leads")
    SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
    SLACK_ESCALATION_CHANNEL: str = os.getenv("SLACK_ESCALATION_CHANNEL", "#leads-escalados")

    @classmethod
    def is_mock(cls) -> bool:
        return cls.MODE != "real"

    @classmethod
    def validate(cls) -> None:
        if cls.LLM_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            raise RuntimeError(
                "Falta GEMINI_API_KEY. Configúrala en tu .env — es gratis: "
                "generala en https://aistudio.google.com/apikey"
            )
        if cls.LLM_PROVIDER == "anthropic" and not cls.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "Falta ANTHROPIC_API_KEY. Configúrala en tu .env, o cambia "
                "LLM_PROVIDER=gemini para usar la opción gratuita."
            )
        if cls.MODE == "real":
            faltantes = [
                nombre for nombre, valor in [
                    ("GMAIL_CREDENTIALS_PATH", cls.GMAIL_CREDENTIALS_PATH),
                    ("AIRTABLE_API_KEY", cls.AIRTABLE_API_KEY),
                    ("AIRTABLE_BASE_ID", cls.AIRTABLE_BASE_ID),
                    ("SLACK_BOT_TOKEN", cls.SLACK_BOT_TOKEN),
                ] if not valor
            ]
            if faltantes:
                raise RuntimeError(
                    f"MODE=real requiere estas variables: {', '.join(faltantes)}"
                )
