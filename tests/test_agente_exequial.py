"""Pruebas del proyecto exequial: agente de llamada y agente de respuesta."""

from src.agente_llamada.graph import build_graph as build_llamada, graph as grafo_llamada
from src.agente_respuesta.graph import build_graph as build_respuesta, graph as grafo_respuesta
from src.context_cache import context_cache


def test_agente_llamada_compila():
    g = build_llamada()
    assert g is not None
    nombres = {n for n in grafo_llamada.get_graph().nodes}
    assert {"recibir", "procesar", "responder"} <= nombres


def test_agente_respuesta_compila():
    g = build_respuesta()
    assert g is not None
    nombres = {n for n in grafo_respuesta.get_graph().nodes}
    assert {"recibir", "procesar", "responder"} <= nombres


def test_agente_llamada_respuesta_sin_api_key():
    from langchain_core.messages import HumanMessage

    estado = {
        "messages": [HumanMessage(content="Necesito información sobre servicios funerarios.")],
        "saltos": [],
        "session_id": "test-llamada-001",
    }
    resultado = grafo_llamada.invoke(estado)
    assert "messages" in resultado
    assert any(getattr(m, "content", "") for m in resultado["messages"])


def test_agente_respuesta_respuesta_sin_api_key():
    from langchain_core.messages import HumanMessage

    estado = {
        "messages": [HumanMessage(content="¿Cuáles son los planes funerarios?")],
        "saltos": [],
        "session_id": "test-respuesta-001",
    }
    resultado = grafo_respuesta.invoke(estado)
    assert "messages" in resultado
    assert any(getattr(m, "content", "") for m in resultado["messages"])


def test_context_cache_memoria_fallback():
    """El caché funciona en memoria cuando Redis no está disponible."""
    context_cache.set("test-sesion-001", {"dato": "valor"})
    recuperado = context_cache.get("test-sesion-001")
    assert recuperado == {"dato": "valor"}
    context_cache.delete("test-sesion-001")
    assert context_cache.get("test-sesion-001") is None


def test_blueprint_json_valido():
    import json

    with open("blueprint.json", encoding="utf-8") as f:
        blueprint = json.load(f)
    assert blueprint["proyecto"] == "proyecto-2-agentes-comerciales-exequial"
    assert blueprint["sector"] == "exequial"
    assert len(blueprint["agentes"]) == 2
    assert blueprint["fallback"]["modo_simulacion_sin_api_key"] is True
