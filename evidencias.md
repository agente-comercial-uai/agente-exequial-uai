# Evidencias — Taller 2 · Entrega local reproducible

Proyecto: Agente Conversacional Exequial
Opción elegida: Servicio FastAPI (`POST /chat`) + canal Telegram.
Integrantes: Leonardo Quezada, José Vilches, José Vilches B, Alex Bravo.

> NOTA: las claves reales NO aparecen aquí. Se omite el valor del token
> (`API_TOKEN`) y del secreto de Telegram en toda captura.
> Todo es entorno LOCAL, fecha de pruebas: 17-noviembre-2026.

---

## Caso 1 — Acceso autorizado (token correcto)

| Campo | Detalle |
|---|---|
| Entorno y fecha | LOCAL · 17-nov-2026 |
| Solicitud | `POST /chat` con cabecera `Authorization: Bearer <API_TOKEN>` y mensaje "hola" |
| Resultado esperado | HTTP 200 con `ruta`, `motivo` y `respuesta` |
| Resultado obtenido | ✅ 200 · ruta `generica` · respuesta empática del agente |
| Evidencia | log: `INFO agente-exequial petición | ruta=generica | duración=11.3 ms | fallo=no` |
| Observaciones | La respuesta es generada por el modelo real (Gemini). |

---

## Caso 2 — Acceso rechazado sin token

| Campo | Detalle |
|---|---|
| Entorno y fecha | LOCAL · 17-nov-2026 |
| Solicitud | `POST /chat` SIN cabecera `Authorization` |
| Resultado esperado | HTTP 401 No autorizado |
| Resultado obtenido | ✅ 401 `{"detail":"No autorizado"}` |
| Evidencia | log: `WARNING agente-exequial acceso rechazado: token inválido o ausente` |
| Observaciones | El endpoint no procesa la petición sin token. |

---

## Caso 3 — Acceso rechazado con token inválido

| Campo | Detalle |
|---|---|
| Entorno y fecha | LOCAL · 17-nov-2026 |
| Solicitud | `POST /chat` con `Authorization: Bearer token_malo` |
| Resultado esperado | HTTP 401 No autorizado |
| Resultado obtenido | ✅ 401 `{"detail":"No autorizado"}` |
| Evidencia | log: `WARNING agente-exequial acceso rechazado` |
| Observaciones | Un token correcto (`Bearer <API_TOKEN>`) sí responde 200. |

---

## Caso 4 — Pruebas automatizadas (33 tests)

| Campo | Detalle |
|---|---|
| Entorno y fecha | LOCAL · 17-nov-2026 |
| Solicitud | `pytest tests/ -q` |
| Resultado esperado | Todos los tests pasan |
| Resultado obtenido | ✅ `33 passed` |
| Evidencia | 33 = 25 originales + 2 nuevos (acceso rechazado) + ajustes de cabeceras |
| Observaciones | Incluye tests de rechazo 401 en `/chat`. |

---

## Caso 5 — Salida `--saltos` del agente (CLI)

| Campo | Detalle |
|---|---|
| Entorno y fecha | LOCAL · 17-nov-2026 |
| Solicitud | `python main.py agente_exequial "hola" --saltos` |
| Resultado esperado | Lista de nodos visitados: `entrada` → `responder` |
| Resultado obtenido | ✅ `1. entrada` · `2. responder` |
| Evidencia | salida del CLI (`main.py`) |
| Observaciones | Los saltos confirman el recorrido del grafo. |

---

## Caso 6 — Endpoint de salud

| Campo | Detalle |
|---|---|
| Entorno y fecha | LOCAL · 17-nov-2026 |
| Solicitud | `GET /health` |
| Resultado esperado | HTTP 200 `{"status":"healthy"}` |
| Resultado obtenido | ✅ 200 `{"status":"healthy"}` |
| Observaciones | Disponible sin token (es un healthcheck). |

---

## Errores / límites detectados

- Sin token: 401 (correcto).
- Modelo sin `GOOGLE_API_KEY`: modo simulación (declarado en README).
- El historial de conversación no se conserva entre peticiones de `/chat` (límite conocido).
- Telegram valida por `X-Telegram-Bot-Api-Secret-Token`; `/chat` valida por `Authorization: Bearer` (dos mecanismos distintos, documentados).
