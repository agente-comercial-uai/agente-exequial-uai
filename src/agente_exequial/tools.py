"""Herramientas del router exequial.

Placeholder para futuras integraciones. Actualmente no hay herramientas
externas conectadas (sin Telegram, WhatsApp, Gmail ni web en esta etapa).
"""

from langchain_core.tools import tool


@tool
def registrar_interaccion(session_id: str, ruta: str, motivo: str) -> str:
    """Registra metadatos de la interacción en caché de sesión.

    Argumentos:
        session_id: identificador de la conversación.
        ruta: ruta clasificada por el router.
        motivo: motivo de la clasificación.
    """
    if not session_id or not session_id.strip():
        return "No se proporcionó un identificador de sesión válido."
    return (
        f"Interacción registrada para sesión {session_id}: "
        f"ruta={ruta}, motivo={motivo}."
    )
