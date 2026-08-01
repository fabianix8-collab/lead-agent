"""
Evaluación sistemática del agente: corre un set de casos con resultado
esperado y mide qué tan bien decide, no solo si "corre sin errores".

Esto es lo que separa un prototipo de un sistema evaluado: en vez de
mirar 6 outputs a ojo, medimos accuracy de clasificación, precisión/recall
de escalamiento, y guardamos el detalle para poder comparar entre
versiones del prompt.

Correr con: python -m eval.run_eval
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from rich.console import Console
from rich.table import Table

from agent import LeadAgent

console = Console()

_CASES_PATH = os.path.join(os.path.dirname(__file__), "cases.json")
_RESULTS_PATH = os.path.join(os.path.dirname(__file__), "eval_results.json")

# El free tier de Gemini limita a 15 solicitudes/minuto por modelo. Cada lead
# puede usar 2-3 llamadas (clasificar + acción + resumen), así que espaciamos
# los casos para no agotar la cuota a mitad de la evaluación.
_PAUSA_ENTRE_CASOS_SEGUNDOS = 8


def _extraer_comportamiento(log: dict) -> dict:
    """Reduce el log crudo del agente a las señales que evaluamos."""
    tools_llamadas = [p["tool"] for p in log["pasos"]]

    prioridad = None
    for p in log["pasos"]:
        if p["tool"] == "clasificar_lead":
            prioridad = p["input"].get("prioridad")

    return {
        "escalo": "escalar_a_humano" in tools_llamadas,
        "agendo": "agendar_reunion" in tools_llamadas,
        "prioridad_detectada": prioridad,
    }


def correr_evaluacion():
    with open(_CASES_PATH, encoding="utf-8") as f:
        casos = json.load(f)

    agent = LeadAgent()
    resultados = []

    tabla = Table(title="Resultados de evaluación")
    tabla.add_column("Caso")
    tabla.add_column("Descripción", max_width=35)
    tabla.add_column("Escalar\n(esp. vs real)")
    tabla.add_column("Prioridad\n(esp. vs real)")
    tabla.add_column("OK")

    aciertos_escalamiento = 0
    aciertos_prioridad = 0
    total_con_prioridad_esperada = 0

    for i, caso in enumerate(casos):
        if i > 0:
            time.sleep(_PAUSA_ENTRE_CASOS_SEGUNDOS)

        log = agent.procesar_lead(caso["lead"])
        real = _extraer_comportamiento(log)
        esperado = caso["esperado"]

        escalamiento_ok = real["escalo"] == esperado["debe_escalar"]
        if escalamiento_ok:
            aciertos_escalamiento += 1

        prioridad_ok = True
        if esperado["prioridad"] is not None:
            total_con_prioridad_esperada += 1
            prioridad_ok = real["prioridad_detectada"] == esperado["prioridad"]
            if prioridad_ok:
                aciertos_prioridad += 1

        todo_ok = escalamiento_ok and prioridad_ok

        resultados.append({
            "id": caso["id"],
            "descripcion": caso["descripcion"],
            "esperado": esperado,
            "real": real,
            "ok": todo_ok,
            "nota": caso["esperado"].get("nota"),
        })

        tabla.add_row(
            caso["id"],
            caso["descripcion"],
            f"{esperado['debe_escalar']} / {real['escalo']}",
            f"{esperado['prioridad']} / {real['prioridad_detectada']}",
            "✅" if todo_ok else "❌",
        )

    console.print(tabla)

    n = len(casos)
    console.print(f"\n[bold]Accuracy de escalamiento:[/bold] {aciertos_escalamiento}/{n} ({aciertos_escalamiento/n:.0%})")
    if total_con_prioridad_esperada:
        console.print(
            f"[bold]Accuracy de clasificación de prioridad:[/bold] "
            f"{aciertos_prioridad}/{total_con_prioridad_esperada} "
            f"({aciertos_prioridad/total_con_prioridad_esperada:.0%})"
        )

    fallidos = [r for r in resultados if not r["ok"]]
    if fallidos:
        console.print(f"\n[bold red]Casos fallidos ({len(fallidos)}):[/bold red]")
        for r in fallidos:
            console.print(f"  - {r['id']}: {r['descripcion']}")
            if r["nota"]:
                console.print(f"    [dim]{r['nota']}[/dim]")

    with open(_RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    console.print(f"\n[dim]Detalle completo guardado en eval/eval_results.json[/dim]")


if __name__ == "__main__":
    correr_evaluacion()
