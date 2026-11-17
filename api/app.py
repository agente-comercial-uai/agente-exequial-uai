"""API FastAPI para el router exequial.

Levantar con:
    uvicorn api.app:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()

from src.agente_exequial.graph import graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("agente-exequial")

app = FastAPI(title="Agente Conversacional Exequial API", version="0.1.0")

# CONFIGURACIÓN OBLIGATORIA: CORS permitiendo todos los orígenes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    conversation_id: str
    message: str


class ChatResponse(BaseModel):
    ruta: str
    motivo: str
    respuesta: str


def _texto_de_mensajes(mensajes) -> str:
    """Devuelve el último texto plano generado por el modelo.

    Los mensajes de langchain-google-genai llegan como lista de bloques
    ({"type": "text", "text": ...}); otros proveedores devuelven un string.
    """
    for m in reversed(mensajes):
        contenido = getattr(m, "content", "") or ""
        if isinstance(contenido, list):
            texto = "".join(
                bloque.get("text", "")
                for bloque in contenido
                if isinstance(bloque, dict) and bloque.get("type") == "text"
            )
            if texto.strip():
                return texto
        elif isinstance(contenido, str) and contenido.strip():
            return contenido
    return ""


def _requerir_token(authorization: Optional[str]) -> None:
    """Valida el token de acceso de la API (Bearer <API_TOKEN>).

    La clave vive en la variable de entorno API_TOKEN. Si está ausente o no
    coincide, responde 401 y no procesa la petición.
    """
    esperado = os.getenv("API_TOKEN", "").strip()
    if not esperado:
        logger.error("API_TOKEN no configurada en el entorno")
        raise HTTPException(status_code=503, detail="Servicio no configurado")

    recibido = (authorization or "").strip()
    if recibido != f"Bearer {esperado}":
        logger.warning("acceso rechazado: token inválido o ausente")
        raise HTTPException(status_code=401, detail="No autorizado")


@app.get("/")
def root():
    return {"mensaje": "API de agente exequial. POST /chat para enviar un mensaje."}


@app.get("/health")
def health():
    """Healthcheck para Heroku y monitoreo."""
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
def chat(
    req: ChatRequest,
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    """Recibe identificador de conversación y texto, invoca el grafo exequial
    y devuelve la ruta, el motivo y la respuesta textual.

    Protegido por un token de acceso en la cabecera `Authorization: Bearer <API_TOKEN>`.
    """
    _requerir_token(authorization)

    inicio = time.perf_counter()
    try:
        estado_inicial = {
            "messages": [HumanMessage(content=req.message)],
            "saltos": [],
            "session_id": req.conversation_id,
            "ruta": "",
            "motivo": "",
            "derivacion_humana": False,
        }

        estado_final = graph.invoke(estado_inicial)

        ruta = estado_final.get("ruta", "")
        motivo = estado_final.get("motivo", "")

        mensajes = estado_final.get("messages", [])
        respuesta = _texto_de_mensajes(mensajes)

        if not respuesta:
            respuesta = "No se pudo generar una respuesta. Intenta de nuevo."

        ms = (time.perf_counter() - inicio) * 1000
        logger.info(
            "petición | conversación=%s | ruta=%s | duración=%.1f ms | fallo=no",
            req.conversation_id,
            ruta,
            ms,
        )

        return ChatResponse(
            ruta=ruta,
            motivo=motivo,
            respuesta=respuesta,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        ms = (time.perf_counter() - inicio) * 1000
        logger.error(
            "petición | conversación=%s | duración=%.1f ms | fallo=sí | error=%s",
            req.conversation_id,
            ms,
            type(exc).__name__,
        )
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@app.post("/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: Optional[str] = Header(
        None, alias="X-Telegram-Bot-Api-Secret-Token"
    ),
):
    """Webhook de Telegram.

    Recibe actualizaciones, valida el secreto, extrae chat_id y texto,
    invoca el grafo exequial y envía la respuesta mediante la API oficial
    de Telegram. Ignora actualizaciones sin texto.
    """
    # Validar secreto de Telegram.
    telegram_secret = os.getenv("TELEGRAM_SECRET", "")
    if not telegram_secret or x_telegram_bot_api_secret_token != telegram_secret:
        raise HTTPException(status_code=401, detail="No autorizado")

    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Cuerpo inválido")

    # Ignorar actualizaciones sin mensaje de texto.
    message = payload.get("message") or payload.get("edited_message")
    if not message:
        return {"ok": True}

    texto = message.get("text")
    if not texto:
        return {"ok": True}

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return {"ok": True}

    # Invocar grafo existente con chat_id como identificador de conversación.
    estado_inicial = {
        "messages": [HumanMessage(content=str(texto))],
        "saltos": [],
        "session_id": str(chat_id),
        "ruta": "",
        "motivo": "",
        "derivacion_humana": False,
    }

    estado_final = graph.invoke(estado_inicial)

    mensajes = estado_final.get("messages", [])
    respuesta = _texto_de_mensajes(mensajes)

    if not respuesta:
        respuesta = "Lo siento, no pude procesar tu mensaje en este momento."

    # Enviar respuesta mediante la API oficial de Telegram.
    telegram_token = os.getenv("TELEGRAM_TOKEN", "")
    if telegram_token:
        try:
            url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
            with httpx.Client(timeout=10.0) as cliente:
                cliente.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": respuesta,
                        "parse_mode": "Markdown",
                    },
                )
        except Exception:  # noqa: BLE001
            # No exponer errores internos al cliente de Telegram.
            pass

    return {"ok": True}
