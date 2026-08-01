"""
Conector de escalamiento a humano. En modo mock imprime la notificación
formateada en consola (con rich) en vez de enviarla a Slack.
"""
from rich.console import Console
from rich.panel import Panel

_console = Console()


class SlackConnector:
    def __init__(self, mock: bool = True):
        self.mock = mock

    def escalar(self, motivo: str, resumen_para_humano: str) -> dict:
        if self.mock:
            _console.print(
                Panel(
                    f"[bold]Motivo:[/bold] {motivo}\n\n{resumen_para_humano}",
                    title="🔔 ESCALADO A HUMANO (simulado)",
                    border_style="yellow",
                )
            )
            return {"status": "ok", "modo": "mock", "canal": "consola"}

        # --- Implementación real (requiere slack-sdk) ---
        # from slack_sdk import WebClient
        # from config import Config
        # client = WebClient(token=Config.SLACK_BOT_TOKEN)
        # client.chat_postMessage(
        #     channel=Config.SLACK_ESCALATION_CHANNEL,
        #     text=f"*Motivo:* {motivo}\n{resumen_para_humano}",
        # )
        # return {"status": "ok", "modo": "real", "canal": Config.SLACK_ESCALATION_CHANNEL}
        raise NotImplementedError(
            "Instala slack-sdk y descomenta la implementación real en slack_notify.py"
        )
