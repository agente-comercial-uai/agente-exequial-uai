"""Pruebas de API para el endpoint POST /chat.

Ejecución: pytest tests/test_api_chat.py -v
Usa TestClient (transporte simulado, sin red real, sin llamadas al modelo real).

El endpoint /chat exige un token en la cabecera `Authorization: Bearer <API_TOKEN>`.
"""

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)

# Token de prueba para las solicitudes autorizadas. Debe coincidir con la
# variable de entorno API_TOKEN; en los tests la leemos del entorno.
import os

TOKEN = os.getenv("API_TOKEN", "tokentest123")
CABECERA = {"Authorization": f"Bearer {TOKEN}"}


def test_chat_necesidad_inmediata():
    response = client.post(
        "/chat",
        json={
            "conversation_id": "conv-001",
            "message": "Mi familiar falleció en el hospital, necesito servicio funerario urgente.",
        },
        headers=CABECERA,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ruta"] == "necesidad_inmediata"
    assert data["motivo"]
    assert data["respuesta"]


def test_chat_necesidad_futura():
    response = client.post(
        "/chat",
        json={
            "conversation_id": "conv-002",
            "message": "Quiero información sobre planes funerarios futuros y previsión exequial.",
        },
        headers=CABECERA,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ruta"] == "necesidad_futura"
    assert data["motivo"]
    assert data["respuesta"]


def test_chat_postventa():
    response = client.post(
        "/chat",
        json={
            "conversation_id": "conv-003",
            "message": "Tengo un servicio contratado y quiero presentar un reclamo.",
        },
        headers=CABECERA,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ruta"] == "postventa"
    assert data["motivo"]
    assert data["respuesta"]


def test_chat_generica():
    response = client.post(
        "/chat",
        json={
            "conversation_id": "conv-004",
            "message": "Hola, buenos días.",
        },
        headers=CABECERA,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ruta"] == "generica"
    assert data["motivo"]
    assert data["respuesta"]


def test_chat_solicitud_atencion_humana():
    response = client.post(
        "/chat",
        json={
            "conversation_id": "conv-005",
            "message": "Quiero hablar con un asesor humano sobre mi servicio.",
        },
        headers=CABECERA,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ruta"] == "derivacion_humana"
    assert data["derivacion_humana"] if "derivacion_humana" in data else True
    assert data["motivo"]
    assert data["respuesta"]


def test_chat_campos_obligatorios():
    # Falta conversation_id
    response = client.post("/chat", json={"message": "hola"}, headers=CABECERA)
    assert response.status_code == 422

    # Falta message
    response = client.post("/chat", json={"conversation_id": "x"}, headers=CABECERA)
    assert response.status_code == 422


def test_chat_respuesta_tiene_campos_esperados():
    response = client.post(
        "/chat",
        json={"conversation_id": "conv-006", "message": "Necesito ayuda urgente."},
        headers=CABECERA,
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"ruta", "motivo", "respuesta"}


def test_chat_sin_token_es_rechazado():
    """Acceso rechazado: sin cabecera Authorization debe dar 401."""
    response = client.post(
        "/chat",
        json={"conversation_id": "conv-007", "message": "hola"},
    )
    assert response.status_code == 401


def test_chat_token_invalido_es_rechazado():
    """Acceso rechazado: token incorrecto debe dar 401."""
    response = client.post(
        "/chat",
        json={"conversation_id": "conv-008", "message": "hola"},
        headers={"Authorization": "Bearer token_malo"},
    )
    assert response.status_code == 401
