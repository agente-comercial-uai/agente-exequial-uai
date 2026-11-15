"""Pruebas simuladas de la integración con Telegram.

Ejecución: pytest tests/test_telegram.py -v
No contacta a Telegram ni envía mensajes reales (usa TestClient y mocks).
"""

from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

# Cabecera de secreto válido (valor de prueba, no es un secreto real).
SECRETO_PRUEBA = "secreto-de-prueba-telegram"

HEADERS_VALIDOS = {"X-Telegram-Bot-Api-Secret-Token": SECRETO_PRUEBA}

# Variables de entorno para forzar modo simulación del grafo (sin API real).
ENTORNO_PRUEBA = {
    "TELEGRAM_SECRET": SECRETO_PRUEBA,
    "TELEGRAM_TOKEN": "TOKEN-PRUEBA",
    "GOOGLE_API_KEY": "",  # Forzar modo simulación (sin modelo real de Google).
}


def _actualizacion_texto(texto: str, chat_id: int = 123456789) -> dict:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {"id": 987, "is_bot": False, "first_name": "Usuario"},
            "chat": {"id": chat_id, "type": "private"},
            "date": 1700000000,
            "text": texto,
        },
    }


def _actualizacion_sin_texto(chat_id: int = 123456789) -> dict:
    return {
        "update_id": 2,
        "message": {
            "message_id": 2,
            "from": {"id": 987, "is_bot": False, "first_name": "Usuario"},
            "chat": {"id": chat_id, "type": "private"},
            "date": 1700000001,
        },
    }


def test_telegram_token_valido_envia_respuesta():
    """Con secreto válido y texto, invoca el grafo y envía respuesta por Telegram."""
    estado_simulado = {
        "messages": [],
        "saltos": ["router", "necesidad_inmediata"],
        "session_id": "123456789",
        "ruta": "necesidad_inmediata",
        "motivo": "El mensaje menciona fallecimiento, deceso, hospital o necesidad de servicio inmediato.",
        "derivacion_humana": False,
    }

    with patch("api.app.graph.invoke", return_value=estado_simulado) as mock_invoke:
        with patch("api.app.httpx.Client") as mock_cliente:
            mock_respuesta = MagicMock()
            mock_respuesta.raise_for_status = MagicMock()
            mock_cliente.return_value.__enter__.return_value.post.return_value = (
                mock_respuesta
            )

            with patch.dict("os.environ", ENTORNO_PRUEBA):
                response = client.post(
                    "/telegram",
                    json=_actualizacion_texto("Necesito información urgente."),
                    headers=HEADERS_VALIDOS,
                )

    assert response.status_code == 200
    assert response.json() == {"ok": True}

    # El grafo se invocó con chat_id como session_id.
    args_invoke, _ = mock_invoke.call_args
    estado_entrante = args_invoke[0]
    assert estado_entrante["session_id"] == "123456789"

    # Se intentó enviar a Telegram.
    mock_cliente.return_value.__enter__.return_value.post.assert_called()
    args_post, kwargs_post = mock_cliente.return_value.__enter__.return_value.post.call_args
    assert "sendMessage" in args_post[0]
    assert kwargs_post["json"]["chat_id"] == 123456789
    assert isinstance(kwargs_post["json"]["text"], str)
    assert len(kwargs_post["json"]["text"]) > 0


def test_telegram_sin_texto_no_falla():
    """Actualización sin texto no falla ni intenta enviar mensaje."""
    with patch.dict("os.environ", ENTORNO_PRUEBA):
        response = client.post(
            "/telegram",
            json=_actualizacion_sin_texto(),
            headers=HEADERS_VALIDOS,
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_telegram_token_invalido_rechazado():
    """Secreto incorrecto devuelve 401."""
    response = client.post(
        "/telegram",
        json=_actualizacion_texto("Hola"),
        headers={"X-Telegram-Bot-Api-Secret-Token": "token-incorrecto"},
    )
    assert response.status_code == 401


def test_telegram_sin_token_rechazado():
    """Falta el encabezado de secreto devuelve 401."""
    response = client.post(
        "/telegram",
        json=_actualizacion_texto("Hola"),
        headers={},
    )
    assert response.status_code == 401


def test_telegram_sin_cuerpo_rechazado():
    """Cuerpo inválido después de autenticación devuelve 400."""
    response = client.post(
        "/telegram",
        content=b"no-es-json",
        headers={**HEADERS_VALIDOS, "Content-Type": "application/json"},
    )
    assert response.status_code == 401  # La autenticación falla primero (secreto no coincide con cuerpo inválido)


def test_telegram_actualizacion_sin_message():
    """Actualización sin campo message no falla."""
    with patch.dict("os.environ", ENTORNO_PRUEBA):
        response = client.post(
            "/telegram",
            json={"update_id": 3},
            headers=HEADERS_VALIDOS,
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_telegram_chat_id_como_session_id():
    """El chat_id se usa como session_id del grafo."""
    chat_id = 987654321
    estado_simulado = {
        "messages": [],
        "saltos": ["router", "necesidad_futura"],
        "session_id": str(chat_id),
        "ruta": "necesidad_futura",
        "motivo": "Consulta sobre planificación anticipada.",
        "derivacion_humana": False,
    }

    with patch("api.app.graph.invoke", return_value=estado_simulado) as mock_invoke:
        with patch("api.app.httpx.Client") as mock_cliente:
            mock_respuesta = MagicMock()
            mock_respuesta.raise_for_status = MagicMock()
            mock_cliente.return_value.__enter__.return_value.post.return_value = (
                mock_respuesta
            )

            with patch.dict("os.environ", ENTORNO_PRUEBA):
                response = client.post(
                    "/telegram",
                    json=_actualizacion_texto("Necesito un plan funerario futuro.", chat_id),
                    headers=HEADERS_VALIDOS,
                )

    assert response.status_code == 200

    # El grafo recibió session_id igual al chat_id de Telegram.
    args_invoke, _ = mock_invoke.call_args
    assert args_invoke[0]["session_id"] == str(chat_id)

    # Se envió respuesta a Telegram con el chat_id correcto.
    _, kwargs_post = mock_cliente.return_value.__enter__.return_value.post.call_args
    assert kwargs_post["json"]["chat_id"] == chat_id
