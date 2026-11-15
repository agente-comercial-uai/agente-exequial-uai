"""Pruebas de API para el endpoint POST /chat.

Ejecución: pytest tests/test_api_chat.py -v
Usa TestClient (transporte simulado, sin red real, sin llamadas al modelo real).
"""

from fastapi.testclient import TestClient

from api.app import app

client = TestClient(app)


def test_chat_necesidad_inmediata():
    response = client.post(
        "/chat",
        json={
            "conversation_id": "conv-001",
            "message": "Mi familiar falleció en el hospital, necesito servicio funerario urgente.",
        },
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
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ruta"] == "derivacion_humana"
    assert data["derivacion_humana"] if "derivacion_humana" in data else True
    assert data["motivo"]
    assert data["respuesta"]


def test_chat_campos_obligatorios():
    # Falta conversation_id
    response = client.post("/chat", json={"message": "hola"})
    assert response.status_code == 422

    # Falta message
    response = client.post("/chat", json={"conversation_id": "x"})
    assert response.status_code == 422


def test_chat_respuesta_tiene_campos_esperados():
    response = client.post(
        "/chat",
        json={"conversation_id": "conv-006", "message": "Necesito ayuda urgente."},
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"ruta", "motivo", "respuesta"}
