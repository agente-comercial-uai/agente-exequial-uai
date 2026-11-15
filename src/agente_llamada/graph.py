"""Grafo LangGraph del agente de llamada (recepción y triage exequial).

Solo construye y compila el grafo. Los prompts viven en prompts.py y las herramientas en tools.py.
"""

from typing import List

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END

from .prompts import SYSTEM_PROMPT_RECEPCION_LLAMADA
from .tools import registrar_datos_llamada, validar_urgencia
from src.context_cache import context_cache


class Estado(dict):
    """Estado del grafo: mensajes, saltos y session_id para caché."""
    messages: List[BaseMessage]
    saltos: List[str]
    session_id: str


def _obtener_modelo():
    """Devuelve un modelo de chat. Usa GOOGLE_API_KEY si está disponible;
    si no, usa un modelo simulado para que el proyecto funcione sin clave real."""
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
            return AIMessage(
                content=(
                    f"[modo simulación, modelo {self.nombre}] "
                    f"Recibí tu mensaje: '{ultimo[:120]}'. "
                    "Configura GOOGLE_API_KEY en .env para usar el modelo real."
                )
            )

    return _ModeloSimulado(modelo)


def _guardar_contexto(state: Estado, clave: str, valor: str) -> None:
    """Guarda un dato en el context cache de la sesión."""
    session_id = state.get("session_id", "default")
    contexto = context_cache.get(session_id) or {}
    contexto[clave] = valor
    context_cache.set(session_id, contexto)


# Nodos ---------------------------------------------------------------

def nodo_recibir(state: Estado) -> Estado:
    """Valida el mensaje de entrada y lo prepara para procesar."""
    saltos = list(state.get("saltos", []))
    saltos.append("recibir")

    mensajes = list(state.get("messages", []))
    if not mensajes:
        mensajes = [HumanMessage(content="")]
    ultimo = mensajes[-1].content if mensajes else ""

    if not str(ultimo).strip():
        respuesta = AIMessage(
            content="Por favor, escribe o comparte tu consulta para poder atenderte."
        )
        return {"messages": mensajes + [respuesta], "saltos": saltos, "session_id": state.get("session_id", "default")}

    sistema = SystemMessage(content=SYSTEM_PROMPT_RECEPCION_LLAMADA)
    return {
        "messages": [sistema] + mensajes,
        "saltos": saltos,
        "session_id": state.get("session_id", "default"),
    }


def nodo_procesar(state: Estado) -> Estado:
    """Analiza la llamada, usa herramientas de registro y urgencia, y guarda contexto."""
    saltos = list(state.get("saltos", []))
    saltos.append("procesar")

    mensajes = list(state.get("messages", []))
    modelo = _obtener_modelo()

    bind_tools = getattr(modelo, "bind_tools", None)
    if bind_tools is not None:
        modelo_con_tools = bind_tools([registrar_datos_llamada, validar_urgencia])
        respuesta = modelo_con_tools.invoke(mensajes)

        tool_calls = getattr(respuesta, "tool_calls", None) or []
        if tool_calls:
            mensajes = mensajes + [respuesta]
            for llamada in tool_calls:
                if isinstance(llamada, dict):
                    nombre = llamada.get("name", "")
                    args = llamada.get("args", {}) or {}
                    call_id = llamada.get("id", "")
                else:
                    nombre = getattr(llamada, "name", "")
                    args = getattr(llamada, "args", {}) or {}
                    call_id = getattr(llamada, "id", "")

                if nombre == "registrar_datos_llamada":
                    resultado = registrar_datos_llamada.invoke(args)
                elif nombre == "validar_urgencia":
                    resultado = validar_urgencia.invoke(args)
                else:
                    resultado = f"Herramienta desconocida: {nombre}"

                mensajes.append(
                    ToolMessage(content=str(resultado), tool_call_id=str(call_id))
                )
                _guardar_contexto(state, nombre, str(resultado))

            respuesta_final = modelo.invoke(
                mensajes + [SystemMessage(content=SYSTEM_PROMPT_RECEPCION_LLAMADA)]
            )
            return {
                "messages": mensajes + [respuesta_final],
                "saltos": saltos,
                "session_id": state.get("session_id", "default"),
            }

    respuesta_final = modelo.invoke(
        mensajes + [SystemMessage(content=SYSTEM_PROMPT_RECEPCION_LLAMADA)]
    )
    return {
        "messages": mensajes + [respuesta_final],
        "saltos": saltos,
        "session_id": state.get("session_id", "default"),
    }


def nodo_responder(state: Estado) -> Estado:
    """Redacta la respuesta final de contención al solicitante."""
    saltos = list(state.get("saltos", []))
    saltos.append("responder")

    mensajes = list(state.get("messages", []))
    modelo = _obtener_modelo()

    respuesta = modelo.invoke(
        mensajes + [SystemMessage(content=SYSTEM_PROMPT_RECEPCION_LLAMADA)]
    )

    return {
        "messages": mensajes + [respuesta],
        "saltos": saltos,
        "session_id": state.get("session_id", "default"),
    }


# Construcción del grafo ----------------------------------------------

def build_graph():
    """Construye y compila el grafo del agente de llamada."""
    constructor = StateGraph(Estado)

    constructor.add_node("recibir", nodo_recibir)
    constructor.add_node("procesar", nodo_procesar)
    constructor.add_node("responder", nodo_responder)

    constructor.set_entry_point("recibir")
    constructor.add_edge("recibir", "procesar")
    constructor.add_edge("procesar", "responder")
    constructor.add_edge("responder", END)

    return constructor.compile()


graph = build_graph()
