"""Herramientas del agente de llamada exequial."""

from langchain_core.tools import tool


@tool
def registrar_datos_llamada(
    nombre_solicitante: str,
    telefono: str,
    parentesco: str,
    estado_actual: str,
    recinto_origen: str,
    comuna: str,
    tipo_servicio: str,
    preferencia: str,
) -> str:
    """
    Registra los datos de la llamada exequial en el contexto de la sesión.

    Argumentos:
        nombre_solicitante: nombre completo de quien llama.
        telefono: número de contacto.
        parentesco: relación con el ser querido.
        estado_actual: 'enfermo grave' o 'fallecido'.
        recinto_origen: hospital, domicilio u otro.
        comuna: comuna o ciudad.
        tipo_servicio: 'inmediato' o 'previsión'.
        preferencia: 'sepultura' o 'cremación'.
    """
    return (
        f"Datos registrados: solicitante={nombre_solicitante}, "
        f"teléfono={telefono}, parentesco={parentesco}, estado={estado_actual}, "
        f"recinto={recinto_origen}, comuna={comuna}, servicio={tipo_servicio}, "
        f"preferencia={preferencia}."
    )


@tool
def validar_urgencia(estado_actual: str, tipo_servicio: str) -> str:
    """
    Determina el nivel de urgencia de la llamada.

    Argumentos:
        estado_actual: 'enfermo grave' o 'fallecido'.
        tipo_servicio: 'inmediato' o 'previsión'.
    """
    if estado_actual.lower() == "fallecido" or tipo_servicio.lower() == "inmediato":
        return "URGENTE: atención inmediata 24/7 asignada. Coordinador de turno activado."
    return "NO URGENTE: servicio de previsión. Agendar seguimiento comercial."
