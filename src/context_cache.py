"""Context cache para el sector exequial.

Intenta usar Redis como backend de contexto y sesiones. Si no hay servidor
Redis disponible, hace fallback automático a un diccionario en memoria.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
TTL_SEGUNDOS = int(os.getenv("CACHE_TTL_SEGUNDOS", "3600"))


class ContextCache:
    """Caché de contexto por sesión (thread_id / número de llamada)."""

    def __init__(self) -> None:
        self._redis = None
        self._memoria: dict[str, dict[str, Any]] = {}
        self._backend = "memoria"

        try:
            import redis  # type: ignore

            self._redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
            self._redis.ping()
            self._backend = "redis"
        except Exception:
            # Redis no disponible: fallback silencioso a memoria.
            self._redis = None
            self._backend = "memoria"

    @property
    def backend(self) -> str:
        return self._backend

    def get(self, session_id: str) -> Optional[dict[str, Any]]:
        clave = f"contexto:{session_id}"
        if self._redis is not None:
            try:
                data = self._redis.get(clave)
                return json.loads(data) if data else None
            except Exception:
                pass
        return self._memoria.get(clave)

    def set(self, session_id: str, valor: dict[str, Any], ttl: int = TTL_SEGUNDOS) -> None:
        clave = f"contexto:{session_id}"
        if self._redis is not None:
            try:
                self._redis.setex(clave, ttl, json.dumps(valor, ensure_ascii=False))
                return
            except Exception:
                pass
        self._memoria[clave] = valor

    def delete(self, session_id: str) -> None:
        clave = f"contexto:{session_id}"
        if self._redis is not None:
            try:
                self._redis.delete(clave)
                return
            except Exception:
                pass
        self._memoria.pop(clave, None)


# Instancia singleton para importar desde cualquier módulo.
context_cache = ContextCache()
