"""Punto de entrada para ejecutar un agente del proyecto exequial.

Uso:
    python main.py {nombre_agente} "mensaje" [--saltos] [--diagrama]

Ejemplos:
    python main.py agente_llamada "Buenos días, necesito información sobre servicios funerarios."
    python main.py agente_respuesta "¿Cuáles son los planes y precios para sepultura en Santiago?"
    python main.py agente_llamada "hola" --saltos
    python main.py agente_respuesta "plan cremación" --diagrama
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()


def _cargar_grafo(nombre_agente: str):
    """Importa src.{nombre_agente}.graph y devuelve el grafo compilado."""
    modulo = importlib.import_module(f"src.{nombre_agente}.graph")
    if hasattr(modulo, "graph"):
        return modulo.graph
    if hasattr(modulo, "build_graph"):
        return modulo.build_graph()
    raise ImportError(
        f"El módulo src.{nombre_agente}.graph no expone `graph` ni `build_graph`."
    )


def _ejecutar(nombre_agente: str, mensaje: str, mostrar_saltos: bool) -> Tuple[str, list]:
    """Ejecuta el grafo del agente y devuelve (respuesta_texto, saltos)."""
    from langchain_core.messages import HumanMessage

    grafo = _cargar_grafo(nombre_agente)

    estado_inicial = {
        "messages": [HumanMessage(content=mensaje)],
        "saltos": [],
    }

    estado_final = grafo.invoke(estado_inicial)

    saltos = list(estado_final.get("saltos", []))
    mensajes = estado_final.get("messages", [])

    respuesta = ""
    for m in reversed(mensajes):
        contenido = getattr(m, "content", "") or ""
        if contenido:
            respuesta = contenido
            break

    if mostrar_saltos:
        print("Saltos (nodos visitados):")
        for i, nodo in enumerate(saltos, 1):
            print(f"  {i}. {nodo}")
        print()

    return respuesta, saltos


def _diagrama(nombre_agente: str) -> str:
    """Devuelve el Mermaid del grafo sin ejecutarlo."""
    grafo = _cargar_grafo(nombre_agente)
    return grafo.get_graph().draw_mermaid()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Ejecuta un agente LangGraph exequial.")
    parser.add_argument("nombre_agente", help="Nombre del paquete en src/ (agente_llamada o agente_respuesta)")
    parser.add_argument("mensaje", help="Mensaje para el agente")
    parser.add_argument("--saltos", action="store_true", help="Imprime los nodos visitados.")
    parser.add_argument("--diagrama", action="store_true", help="Imprime Mermaid sin ejecutar.")
    args = parser.parse_args(argv)

    if args.diagrama:
        print(_diagrama(args.nombre_agente))
        return 0

    respuesta, _ = _ejecutar(args.nombre_agente, args.mensaje, args.saltos)
    print(respuesta)
    return 0


if __name__ == "__main__":
    sys.exit(main())
