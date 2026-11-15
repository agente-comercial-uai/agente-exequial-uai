"""Scripts para configurar y verificar el webhook de Telegram.

Lee TELEGRAM_TOKEN y PUBLIC_URL del entorno. No contiene secretos
hardcodeados. Ejecutar únicamente con autorización expresa y cuando el
servicio esté expuesto públicamente (p. ej., en Heroku).
"""

from __future__ import annotations

import os
from typing import Optional

import httpx


def _telegram_api_url(metodo: str) -> str:
    token = os.getenv("TELEGRAM_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN no está configurado en el entorno.")
    return f"https://api.telegram.org/bot{token}/{metodo}"


def set_webhook(public_url: Optional[str] = None) -> dict:
    """Configura el webhook de Telegram.

    Argumentos:
        public_url: URL pública https del servicio (p. ej., https://app.herokuapp.com).
                    Si no se pasa, se lee de PUBLIC_URL del entorno.
    """
    url = public_url or os.getenv("PUBLIC_URL", "")
    if not url:
        raise RuntimeError("PUBLIC_URL no está configurada en el entorno.")

    webhook_url = f"{url.rstrip('/')}/telegram"

    with httpx.Client(timeout=15.0) as cliente:
        respuesta = cliente.post(
            _telegram_api_url("setWebhook"),
            json={"url": webhook_url, "secret_token": os.getenv("TELEGRAM_SECRET", "")},
        )
        respuesta.raise_for_status()
        return respuesta.json()


def get_webhook_info() -> dict:
    """Devuelve información actual del webhook configurado."""
    with httpx.Client(timeout=15.0) as cliente:
        respuesta = cliente.get(_telegram_api_url("getWebhookInfo"))
        respuesta.raise_for_status()
        return respuesta.json()


def delete_webhook() -> dict:
    """Elimina el webhook configurado."""
    with httpx.Client(timeout=15.0) as cliente:
        respuesta = cliente.post(_telegram_api_url("deleteWebhook"))
        respuesta.raise_for_status()
        return respuesta.json()


if __name__ == "__main__":  # pragma: no cover
    import sys

    comando = sys.argv[1] if len(sys.argv) > 1 else "info"

    if comando == "set":
        print(set_webhook())
    elif comando == "info":
        print(get_webhook_info())
    elif comando == "delete":
        print(delete_webhook())
    else:
        print("Uso: python scripts/telegram_webhook.py {set|info|delete}")
