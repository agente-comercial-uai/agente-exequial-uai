"""Grafo LangGraph del router exequial.

Solo construye y compila el grafo. Los prompts de cada nodo viven en
prompts.py y las herramientas en tools.py.
"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

from .prompts import (
    SYSTEM_PROMPT_ROUTER,
    SYSTEM_PROMPT_NECESIDAD_INMEDIATA,
    SYSTEM_PROMPT_NECESIDAD_FUTURA,
    SYSTEM_PROMPT_POSTVENTA,
    SYSTEM_PROMPT_GENERICA,
    SYSTEM_PROMPT_DERIVACION_HUMANA,
)


class Estado(dict):
    """Estado del grafo del router exequial.

    Campos:
        messages: historial de la conversación.
        saltos: nodos visitados.
        session_id: identificador de conversación/sesión.
        ruta: ruta clasificada por el router.
        motivo: motivo de la clasificación.
        derivacion_humana: si se requiere atención de asesor humano.
    """

    messages: List[BaseMessage]
    saltos: List[str]
    session_id: str
    ruta: str
    motivo: str
    derivacion_humana: bool


def _obtener_modelo():
    """Devuelve un modelo de chat (igual patrón que src/asistente).

    Usa GOOGLE_API_KEY + MODELO del entorno si están disponibles; si no, usa
    un modelo simulado para que el proyecto funcione sin clave real.
    """
    import os

    api_key = os.getenv("GOOGLE_API_KEY")
    modelo = os.getenv("MODELO", "gemini-3.5-flash-lite")

    if api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=modelo, google_api_key=api_key)

    class _ModeloSimulado:
        def __init__(self, nombre: str):
            self.nombre = nombre

        def invoke(self, mensajes):
            ultimo = ""
            for m in reversed(mensajes):
                contenido = getattr(m, "content", "") or ""
                if contenido:
                    ultimo = contenido
                    break
            return AIMessage(
                content=(
                    f"[modo simulación, modelo {self.nombre}] "
                    f"Recibí tu mensaje: '{ultimo[:120]}'. "
                    "Configura GOOGLE_API_KEY en .env para usar el modelo real."
                )
            )

    return _ModeloSimulado(modelo)


# ---------------------------------------------------------------------------
# Clasificación por reglas (heurística en español). No consume tokens del LLM.
# ---------------------------------------------------------------------------

PALABRAS_URGENCIA = [
    "fallecid",
    "muerto",
    "deceso",
    "difunto",
    "urgente",
    "urgencia",
    "ahora",
    "inmediato",
    "hospital",
    "domicilio",
    "recinto",
    "velorio",
    "enterr",
    "sepult",
    "crem",
    "fallecimiento",
]

PALABRAS_FUTURO = [
    "plan",
    "previsión",
    "prevision",
    "futuro",
    "cotiz",
    "cotización",
    "precio",
    "plan funerario",
    "sepultura futura",
    "cremación futura",
    "contratar",
    "planear",
    "planificación",
]

PALABRAS_POSTVENTA = [
    "reclamo",
    "queja",
    "seguimiento",
    "contratado",
    "ya contraté",
    "mi servicio",
    "póliza",
    "siniestro",
    "beneficiario",
    "reembolso",
    "atención postventa",
    "problema con el servicio",
]

PALABRAS_HUMANA = [
    "asesor",
    "asesora",
    "humano",
    "persona",
    "habl con un",
    "atención humana",
    "asesor humano",
    "ejecutivo",
    "llamar",
]


def _clasificar_ruta(texto: str) -> tuple[str, str, bool]:
    """Clasifica el mensaje usando heurística de palabras clave.

    Devuelve (ruta, motivo, derivacion_humana).
    No llama al modelo de lenguaje: cero costo de tokens para clasificación.
    """
    t = texto.lower()
    derivacion = any(p in t for p in PALABRAS_HUMANA)

    # Postventa / reclamos (prioridad: un reclamo sobre un velorio pasado es
    # postventa, no urgencia inmediata).
    if any(p in t for p in PALABRAS_POSTVENTA):
        motivo = (
            "El mensaje hace referencia a un servicio contratado, seguimiento "
            "o reclamo postventa."
        )
        return "postventa", motivo, derivacion

    # Prioridad: urgencia inmediata (fallecimiento reciente, deceso, hospital).
    if any(p in t for p in PALABRAS_URGENCIA):
        motivo = (
            "El mensaje menciona fallecimiento, deceso, hospital o necesidad "
            "de servicio inmediato."
        )
        return "necesidad_inmediata", motivo, derivacion

    # Planificación futura / cotización informativa
    if any(p in t for p in PALABRAS_FUTURO):
        motivo = (
            "El mensaje consulta sobre planes, previsión o planificación "
            "anticipada de servicios exequiales."
        )
        return "necesidad_futura", motivo, derivacion

    # Saludo o genérico
    motivo = (
        "El mensaje es un saludo o una consulta no clasificable como urgencia, "
        "planificación o postventa del sector exequial."
    )
    return "generica", motivo, derivacion


# ---------------------------------------------------------------------------
# Nodos del grafo
# ---------------------------------------------------------------------------

def _ultimo_texto(state) -> str:
    mensajes = list(state.get("messages", []))
    if not mensajes:
        return ""
    return getattr(mensajes[-1], "content", "") or ""


def nodo_router(state: Estado) -> Estado:
    """Clasifica la consulta del usuario en una de las 4 rutas del negocio.

    Produce una decisión estructurada con ruta y motivo. Usa reglas
    determinísticas para clasificar sin consumo de tokens del modelo.
    """
    saltos = list(state.get("saltos", []))
    saltos.append("router")

    texto = _ultimo_texto(state)
    ruta, motivo, derivacion = _clasificar_ruta(texto)

    # Si se solicita atención humana, la ruta de destino es derivacion_humana.
    if derivacion:
        ruta = "derivacion_humana"

    return {
        "messages": list(state.get("messages", [])),
        "saltos": saltos,
        "session_id": state.get("session_id", "default"),
        "ruta": ruta,
        "motivo": motivo,
        "derivacion_humana": derivacion,
    }


def nodo_necesidad_inmediata(state: Estado) -> Estado:
    """Nodo para consultas de necesidad exequial actual o urgente."""
    saltos = list(state.get("saltos", []))
    saltos.append("necesidad_inmediata")

    mensajes = list(state.get("messages", []))
    sistema = SystemMessage(content=SYSTEM_PROMPT_NECESIDAD_INMEDIATA)
    modelo = _obtener_modelo()

    respuesta = modelo.invoke([sistema] + mensajes)

    return {
        "messages": mensajes + [respuesta],
        "saltos": saltos,
        "session_id": state.get("session_id", "default"),
        "ruta": state.get("ruta", "necesidad_inmediata"),
        "motivo": state.get("motivo", ""),
        "derivacion_humana": state.get("derivacion_humana", False),
    }


def nodo_necesidad_futura(state: Estado) -> Estado:
    """Nodo para planificación anticipada y previsión exequial."""
    saltos = list(state.get("saltos", []))
    saltos.append("necesidad_futura")

    mensajes = list(state.get("messages", []))
    sistema = SystemMessage(content=SYSTEM_PROMPT_NECESIDAD_FUTURA)
    modelo = _obtener_modelo()

    respuesta = modelo.invoke([sistema] + mensajes)

    return {
        "messages": mensajes + [respuesta],
        "saltos": saltos,
        "session_id": state.get("session_id", "default"),
        "ruta": state.get("ruta", "necesidad_futura"),
        "motivo": state.get("motivo", ""),
        "derivacion_humana": state.get("derivacion_humana", False),
    }


def nodo_postventa(state: Estado) -> Estado:
    """Nodo para seguimiento, consultas posteriores y reclamos."""
    saltos = list(state.get("saltos", []))
    saltos.append("postventa")

    mensajes = list(state.get("messages", []))
    sistema = SystemMessage(content=SYSTEM_PROMPT_POSTVENTA)
    modelo = _obtener_modelo()

    respuesta = modelo.invoke([sistema] + mensajes)

    return {
        "messages": mensajes + [respuesta],
        "saltos": saltos,
        "session_id": state.get("session_id", "default"),
        "ruta": state.get("ruta", "postventa"),
        "motivo": state.get("motivo", ""),
        "derivacion_humana": state.get("derivacion_humana", False),
    }


def nodo_generica(state: Estado) -> Estado:
    """Nodo para saludos y consultas ajenas al ámbito exequial."""
    saltos = list(state.get("saltos", []))
    saltos.append("generica")

    mensajes = list(state.get("messages", []))
    sistema = SystemMessage(content=SYSTEM_PROMPT_GENERICA)
    modelo = _obtener_modelo()

    respuesta = modelo.invoke([sistema] + mensajes)

    return {
        "messages": mensajes + [respuesta],
        "saltos": saltos,
        "session_id": state.get("session_id", "default"),
        "ruta": state.get("ruta", "generica"),
        "motivo": state.get("motivo", ""),
        "derivacion_humana": state.get("derivacion_humana", False),
    }


def nodo_derivacion_humana(state: Estado) -> Estado:
    """Nodo que informa al usuario que será derivado a un asesor humano."""
    saltos = list(state.get("saltos", []))
    saltos.append("derivacion_humana")

    mensajes = list(state.get("messages", []))
    sistema = SystemMessage(content=SYSTEM_PROMPT_DERIVACION_HUMANA)
    modelo = _obtener_modelo()

    respuesta = modelo.invoke([sistema] + mensajes)

    return {
        "messages": mensajes + [respuesta],
        "saltos": saltos,
        "session_id": state.get("session_id", "default"),
        "ruta": state.get("ruta", "generica"),
        "motivo": state.get("motivo", ""),
        "derivacion_humana": True,
    }


# ---------------------------------------------------------------------------
# Construcción del grafo
# ---------------------------------------------------------------------------

def _ruta_destino(state: Estado) -> str:
    """Selecciona el nodo de destino según la ruta clasificada.

    Si se solicita atención humana, prioriza derivacion_humana.
    """
    if state.get("derivacion_humana"):
        return "derivacion_humana"
    return state.get("ruta", "generica")


def build_graph():
    """Construye y compila el grafo del router exequial."""
    constructor = StateGraph(Estado)

    constructor.add_node("router", nodo_router)
    constructor.add_node("necesidad_inmediata", nodo_necesidad_inmediata)
    constructor.add_node("necesidad_futura", nodo_necesidad_futura)
    constructor.add_node("postventa", nodo_postventa)
    constructor.add_node("generica", nodo_generica)
    constructor.add_node("derivacion_humana", nodo_derivacion_humana)

    constructor.set_entry_point("router")
    constructor.add_conditional_edges(
        "router",
        _ruta_destino,
        {
            "necesidad_inmediata": "necesidad_inmediata",
            "necesidad_futura": "necesidad_futura",
            "postventa": "postventa",
            "generica": "generica",
            "derivacion_humana": "derivacion_humana",
        },
    )
    constructor.add_edge("necesidad_inmediata", END)
    constructor.add_edge("necesidad_futura", END)
    constructor.add_edge("postventa", END)
    constructor.add_edge("generica", END)
    constructor.add_edge("derivacion_humana", END)

    return constructor.compile()


# Grafo compilado listo para importar (una sola vez en el ciclo de vida).
graph = build_graph()
