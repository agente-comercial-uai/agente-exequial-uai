# Tutorial — Taller 2 · Agente Conversacional Exequial

Entrega local reproducible. Guía completa para ejecutar, desplegar y compartir.

**Integrantes:** Leonardo Quezada · José Vilches · José Vilches B · Alex Bravo (25% c/u)
**Opción elegida:** Servicio FastAPI (`POST /chat`) + canal Telegram.
**Fecha:** 17-noviembre-2026

---

## 1. Qué entrega este proyecto

Un agente conversacional para el sector exequial con:

- Router LangGraph que clasifica en 4 rutas (`necesidad_inmediata`, `necesidad_futura`, `postventa`, `generica`) + `derivacion_humana`.
- API FastAPI con `POST /chat` (protegido por token) y `POST /telegram` (webhook con secreto).
- Token de acceso validado en servidor: sin él → `401`.
- Logs por petición (pregunta, duración, fallo).
- 33 pruebas automatizadas.
- Desplegado en Heroku (v23) como +1 opcional.

**Soluciones resueltas en esta entrega:**
1. `/chat` no cargaba `.env` → se agregó `load_dotenv()` (el servidor no leía el token).
2. Mensaje vacío rompía Gemini ("contents are required") → guard que responde texto fijo sin llamar al modelo.
3. Agentes originales fallaban con "prefilling" → `nodo_responder` reutiliza la respuesta ya generada.

---

## 2. Requisitos

- Python 3.12 (Windows)
- Git
- Telegram (celular, para el bot)
- Heroku CLI (solo para la nube)

---

## 3. Ejecutar en LOCAL

### 3.1 Clonar (si partes desde cero)
```powershell
git clone https://github.com/agente-comercial-uai/agente-exequial-uai.git
cd agente-exequial-uai
```

### 3.2 Crear entorno virtual e instalar
```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3.3 Configurar variables
```powershell
Copy-Item .env.example .env
```
Edita `.env` y completa:
```
GOOGLE_API_KEY=tu_clave
MODELO=gemini-3.5-flash-lite
API_TOKEN=tokentest123
TELEGRAM_TOKEN=...
TELEGRAM_SECRET=...
PUBLIC_URL=
```

### 3.4 Levantar la API
```powershell
.venv\Scripts\uvicorn.exe api.app:app --reload --port 8000
```

### 3.5 Probar acceso (autorizado y rechazado)
```powershell
# Con token → 200
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -Headers @{ Authorization = "Bearer tokentest123" } -ContentType "application/json" -Body '{"conversation_id":"demo","message":"Hola"}'

# Sin token → 401
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post -ContentType "application/json" -Body '{"conversation_id":"demo","message":"Hola"}'

# Salud → 200
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

### 3.6 Pruebas y CLI
```powershell
.venv\Scripts\pytest.exe tests/ -q        # 33 passed
.venv\Scripts\python.exe main.py agente_exequial "hola" --saltos
.venv\Scripts\python.exe main.py agente_exequial --diagrama
```

---

## 4. Desplegar en GITHUB

El código ya está en: https://github.com/agente-comercial-uai/agente-exequial-uai

Para subir cambios propios:
```powershell
git add .
git commit -m "mensaje"
git push origin main
```

---

## 5. Desplegar en HEROKU

### 5.1 Instalar y login
```powershell
heroku login
```

### 5.2 Crear app y configurar variables
```powershell
heroku create agente-exequial-uai
heroku config:set GOOGLE_API_KEY="..." MODELO="gemini-3.5-flash-lite" API_TOKEN="exequial-demo-2026" TELEGRAM_TOKEN="..." TELEGRAM_SECRET="..." PUBLIC_URL="https://agente-exequial-uai-711bc0f2af4d.herokuapp.com"
```

### 5.3 Desplegar
```powershell
git push heroku main
heroku open
```

### 5.4 Verificar en nube
```
https://agente-exequial-uai-711bc0f2af4d.herokuapp.com/health
```

---

## 6. Conectar TELEGRAM

1. En Telegram buscar `@BotFather` → `/newbot` → copiar token.
2. Poner `TELEGRAM_TOKEN` y `TELEGRAM_SECRET` en `.env` y en Heroku.
3. Registrar el webhook:
```powershell
.venv\Scripts\python.exe scripts/telegram_webhook.py set
```
4. Probar el bot en Telegram.

---

## 7. Compartir con PROFESORES y COMPAÑEROS

| Qué compartir | Enlace / ruta |
|---|---|
| Código (repo) | https://github.com/agente-comercial-uai/agente-exequial-uai |
| Clonar | `git clone https://github.com/agente-comercial-uai/agente-exequial-uai.git` |
| App en nube | https://agente-exequial-uai-711bc0f2af4d.herokuapp.com |
| Salud nube | https://agente-exequial-uai-711bc0f2af4d.herokuapp.com/health |
| Bot Telegram | `@exequial_bot` |
| ZIP completo | `C:\Users\abravos1970\Documents\Proyecto predeterminado\proyecto-2-agentes-comerciales-exequial.zip` |

**Claves de prueba (por vía privada, nunca en el repo):**
- `API_TOKEN` local: `tokentest123`
- `API_TOKEN` nube: `exequial-demo-2026`
- Secreto Telegram: `ExequialTelegram2026_Secreto`

---

## 8. Evidencias

- `evidencias.md` → 6 casos documentados.
- `como-sacar-evidencias.md` → guion para las capturas.
- Capturas: solo tú las tomas (fotos de terminal/navegador).

---

## 9. Límites conocidos

- Sin `GOOGLE_API_KEY` → modo simulación.
- Caché en memoria si no hay `REDIS_URL` (se pierde al reiniciar).
- `/chat` no conserva historial entre peticiones.
- Falla del modelo → `500` + log.
