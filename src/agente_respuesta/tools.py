"""Herramientas del agente de respuesta comercial exequial."""

from langchain_core.tools import tool


PLANES_FUNERARIOS = {
    "Plan Honor Integral": {
        "cobertura": "urna, carroza, capilla ardiente, trámites de defunción y pase de sepultación",
        "precio_clp": 850000,
    },
    "Plan Paz Tradicional": {
        "cobertura": "urna estándar, carroza, capilla ardiente y trámites básicos",
        "precio_clp": 620000,
    },
    "Plan Cremación Dignidad": {
        "cobertura": "urna para cremación, proceso de cremación y trámites asociados",
        "precio_clp": 480000,
    },
}


@tool
def obtener_planes_funerarios() -> str:
    """
    Devuelve los planes funerarios disponibles con cobertura y precio en CLP.
    """
    lineas = ["Planes funerarios disponibles:"]
    for nombre, datos in PLANES_FUNERARIOS.items():
        lineas.append(
            f"- {nombre}: {datos['cobertura']} — ${datos['precio_clp']:,} CLP"
        )
    return "\n".join(lineas)


@tool
def calcular_cotizacion(plan: str, cantidad_servicios: int = 1) -> str:
    """
    Calcula una cotización aproximada para un plan funerario.

    Argumentos:
        plan: nombre del plan ('Plan Honor Integral', 'Plan Paz Tradicional', 'Plan Cremación Dignidad').
        cantidad_servicios: número de servicios o unidades.
    """
    plan_clean = plan.strip()
    if plan_clean not in PLANES_FUNERARIOS:
        return f"No se encontró el plan '{plan}'. Planes disponibles: {', '.join(PLANES_FUNERARIOS.keys())}."

    precio_unitario = PLANES_FUNERARIOS[plan_clean]["precio_clp"]
    total = precio_unitario * cantidad_servicios
    return (
        f"Cotización para {plan_clean} x{cantidad_servicios}: "
        f"${precio_unitario:,} CLP c/u — Total estimado: ${total:,} CLP. "
        "Sujeto a confirmación final con el coordinador de turno."
    )
