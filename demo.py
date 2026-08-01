"""
Corre el agente sobre los 6 leads de ejemplo y muestra el resultado de
forma legible. Este es el script que corres para la demo en vivo.
"""
import json
from rich.console import Console
from rich.panel import Panel

from agent import LeadAgent
from connectors.gmail_client import GmailConnector
from config import Config

console = Console()


def main():
    gmail = GmailConnector(mock=Config.is_mock())
    leads = gmail.obtener_leads_nuevos()
    agent = LeadAgent()  # factory: instancia Gemini o Anthropic según LLM_PROVIDER

    resultados = []
    escalados = 0

    for lead in leads:
        console.rule(f"[bold cyan]Lead: {lead['nombre']} — {lead['asunto']}")
        log = agent.procesar_lead(lead)
        resultados.append(log)

        for paso in log["pasos"]:
            if paso["tool"] == "escalar_a_humano":
                escalados += 1
            console.print(f"  → [bold]{paso['tool']}[/bold]: {json.dumps(paso['input'], ensure_ascii=False)}")

        console.print(Panel(log.get("resumen_final", ""), title="Resumen del agente", border_style="green"))

    console.rule("[bold magenta]Métricas de la corrida")
    total = len(leads)
    console.print(f"Leads procesados: {total}")
    console.print(f"Escalados a humano: {escalados} ({escalados/total:.0%})")
    console.print(f"Auto-resueltos: {total - escalados} ({(total-escalados)/total:.0%})")

    with open("resultado_demo.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    console.print("\n[dim]Log completo guardado en resultado_demo.json[/dim]")


if __name__ == "__main__":
    main()
