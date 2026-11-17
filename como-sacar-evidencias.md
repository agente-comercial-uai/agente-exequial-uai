# Guion: cómo sacar las capturas (evidencias del Taller 2)

Proyecto: Agente Conversacional Exequial
Fecha de pruebas: ___-___ (escríbelo al momento de capturar)
Entorno: LOCAL

> Cada captura debe ser una imagen (screenshot) legible. No muestres valores
> reales de `API_TOKEN`, `TELEGRAM_SECRET` ni la `GOOGLE_API_KEY`. Ya están
> documentadas en `evidencias.md`; aquí solo ejecutas y capturas.

---

## Captura 1 — Pruebas automatizadas (33 tests)

**Qué ejecuto (PowerShell):**
```powershell
cd "C:\Users\abravos1970\Documents\Proyecto predeterminado\proyecto-2-agentes-comerciales-exequial"
.venv\Scripts\pytest.exe tests/ -q
```

**Qué busco en pantalla:** la línea final:
```
33 passed
```
> (si no sale 33, avísame: pudo no estar la variable `API_TOKEN` en el entorno)

**Capturar:** la terminal mostrando `33 passed`.

---

## Captura 2 — Acceso autorizado (200)

**Qué ejecuto:**
```powershell
$body = '{"conversation_id":"demo","message":"Hola, buenos dias"}'
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post `
  -Headers @{ Authorization = "Bearer tokentest123" } `
  -ContentType "application/json" -Body $body
```

> Antes, el servidor debe estar corriendo en otra ventana:
> ```powershell
> .venv\Scripts\uvicorn.exe api.app:app --reload --port 8000
> ```

**Qué busco:** un JSON de respuesta con `ruta`, `motivo` y `respuesta`.

**Capturar:** la terminal con la respuesta del agente (200). La misma ventana del
servidor muestra el log `INFO agente-exequial petición ...`.

---

## Captura 3 — Acceso rechazado sin token (401)

**Qué ejecuto:**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post `
  -ContentType "application/json" -Body $body
```

**Qué busco:** el error:
```
{(Invoke-RestMethod : The remote server returned an error: (401) Unauthorized.)}
```

**Capturar:** la terminal con el 401. (En la ventana del servidor se ve
`WARNING agente-exequial acceso rechazado`.)

---

## Captura 4 — Endpoint de salud `/health`

**Qué ejecuto (navegador o PowerShell):**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

**Qué busco:** `{"status":"healthy"}`

**Capturar:** el navegador en `http://localhost:8000/health` (o el resultado en terminal).

---

## Captura 5 — Salida `--saltos` del agente

**Qué ejecuto:**
```powershell
.venv\Scripts\python.exe main.py agente_exequial "hola" --saltos
```

**Qué busco:**
```
  1. entrada
  2. responder
```

**Capturar:** la terminal con la lista de nodos.

---

## Captura 6 (opcional, vale +1) — despliegue en nube

**Qué abro:** el navegador en:
```
https://agente-exequial-uai-711bc0f2af4d.herokuapp.com/health
```

**Qué busco:** `{"status":"healthy"}`

**Capturar:** la URL y el JSON en el navegador, mostrando que responde sin tu
computador (prueba de despliegue).

---

# Resumen: 6 capturas

| # | Qué | Dónde |
|---|---|---|
| 1 | `33 passed` | terminal |
| 2 | `/chat` con token → 200 | terminal + log |
| 3 | `/chat` sin token → 401 | terminal |
| 4 | `/health` → healthy | navegador/terminal |
| 5 | `--saltos` → entrada/responder | terminal |
| 6 | Heroku `/health` | navegador (nube) |

Guarda cada captura con nombre: `captura-1.png` ... `captura-6.png`, e incorpóralas
a la entrega junto a `evidencias.md`.
