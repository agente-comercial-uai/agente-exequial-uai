"""Pruebas unitarias del router exequial.

Ejecución: pytest tests/test_router_exequial.py
No requiere GOOGLE_API_KEY (modo simulación). No usa datos reales de clientes.
"""

from src.agente_exequial.graph import build_graph, graph, Estado
from langchain_core.messages import HumanMessage


def _invoke(texto: str, session_id: str = "test-sesion") -> dict:
    estado_inicial: Estado = {
        "messages": [HumanMessage(content=texto)],
        "saltos": [],
        "session_id": session_id,
        "ruta": "",
        "motivo": "",
        "derivacion_humana": False,
    }
    return graph.invoke(estado_inicial)


def test_router_compila():
    g = build_graph()
    assert g is not None


def test_router_tiene_nodos_esperados():
    nombres = {n for n in graph.get_graph().nodes}
    esperados = {
        "router",
        "necesidad_inmediata",
        "necesidad_futura",
        "postventa",
        "generica",
        "derivacion_humana",
    }
    assert esperados <= nombres


def test_clasifica_necesidad_inmediata():
    resultado = _invoke(
        "Mi familiar falleció hace poco en el hospital, necesito servicio funerario urgente."
    )
    assert resultado["ruta"] == "necesidad_inmediata"
    assert resultado["motivo"]
    assert any(getattr(m, "content", "") for m in resultado["messages"])


def test_clasifica_necesidad_futura():
    resultado = _invoke(
        "Quiero información sobre planes funerarios futuros y previsión exequial."
    )
    assert resultado["ruta"] == "necesidad_futura"
    assert resultado["motivo"]


def test_clasifica_postventa():
    resultado = _invoke(
        "Tengo un servicio contratado y quiero presentar un reclamo por el velorio."
    )
    assert resultado["ruta"] == "postventa"
    assert resultado["motivo"]


def test_clasifica_generica():
    resultado = _invoke("Hola, buenos días. ¿Cómo estás?")
    assert resultado["ruta"] == "generica"
    assert resultado["motivo"]


def test_caso_ambiguo_no_falla():
    resultado = _invoke("Necesito ayuda con algo, no sé exactamente qué.")
    assert resultado["ruta"] in {
        "necesidad_inmediata",
        "necesidad_futura",
        "postventa",
        "generica",
    }
    assert resultado["motivo"]


def test_solicitud_atencion_humana_deriva():
    resultado = _invoke("Quiero hablar con un asesor humano sobre mi servicio.")
    assert resultado["derivacion_humana"] is True
    assert resultado["ruta"] == "derivacion_humana"


def test_mensaje_vacio_no_se_rompe():
    resultado = _invoke("")
    assert resultado["ruta"] in {
        "necesidad_inmediata",
        "necesidad_futura",
        "postventa",
        "generica",
    }


def test_estado_conserva_session_id():
    resultado = _invoke("Hola", session_id="sesion-123")
    assert resultado["session_id"] == "sesion-123"


def test_respuesta_tiene_contenido():
    resultado = _invoke("Necesito información urgente sobre funeral.")
    mensajes = resultado["messages"]
    contenidos = [
        getattr(m, "content", "") for m in mensajes if getattr(m, "content", "")
    ]
    assert len(contenidos) >= 1
