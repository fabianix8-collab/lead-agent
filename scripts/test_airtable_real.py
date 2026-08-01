"""
Prueba la integración REAL de Airtable de forma aislada, sin depender de
MODE global (que activaría también Gmail/Calendar/Slack real, que aún
no están implementados). Útil para verificar la configuración de Airtable
paso a paso antes de correr todo el sistema en modo real.

Requiere en tu .env: AIRTABLE_API_KEY, AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME
(ver README, sección "Configurar Airtable real").

Correr con: python -m scripts.test_airtable_real
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from connectors.crm_airtable import AirtableConnector
from config import Config

console = Console()


def main():
    if not all([Config.AIRTABLE_API_KEY, Config.AIRTABLE_BASE_ID]):
        console.print(
            "[bold red]Faltan credenciales de Airtable en tu .env[/bold red] "
            "(AIRTABLE_API_KEY / AIRTABLE_BASE_ID). Revisa el README, sección "
            "'Configurar Airtable real'."
        )
        return

    console.print("[bold]Creando un contacto de prueba en tu base real de Airtable...[/bold]")

    conector = AirtableConnector(mock=False)  # fuerza modo real, aislado de Config.MODE

    try:
        resultado = conector.crear_contacto(
            nombre="Prueba Lead Agent",
            email="prueba@lead-agent-test.com",
            prioridad="tibio",
            empresa="Empresa de Prueba",
            notas="Registro creado por scripts/test_airtable_real.py — puedes borrarlo de Airtable.",
        )
        console.print(f"[bold green]✅ Éxito:[/bold green] {resultado}")
        console.print(
            "\nVe a tu base de Airtable y confirma que aparece el registro "
            "'Prueba Lead Agent'. Si lo ves, tu integración real está lista."
        )
    except Exception as e:
        console.print(f"[bold red]❌ Falló:[/bold red] {e}")
        console.print(
            "\nRevisa: nombres de columnas exactos (Nombre, Email, Empresa, "
            "Prioridad, Notas), que 'Prioridad' tenga la opción 'tibio' "
            "creada como Single select, y que el token tenga permiso de "
            "escritura sobre esa base."
        )


if __name__ == "__main__":
    main()
