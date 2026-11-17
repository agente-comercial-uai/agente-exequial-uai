# Agente Conversacional Exequial

Agente conversacional para el sector exequial (funerario), con trato empático, orientación comercial ética y derivación a un asesor humano cuando corresponda. Implementado con **Python 3.12**, **LangGraph**, **LangChain**, **Pydantic** y **FastAPI**.

---

## Integrantes y aportes

| Integrante | Aporte |
|-----------|--------|
| Leonardo Quezada | Verificación de reproducción en local y documentación de arranque |
| José Vilches | Evidencias de acceso autorizado y rechazado |
| José Vilches B | Preparación manual y límites conocidos del agente |
| Alex Bravo | Código, seguridad (token) y README |

**Opción elegida:** Servicio FastAPI (canal de uso = API `POST /chat` protegida), complementado con Telegram como canal de atención.

---

## 1. Qué hace el proyecto

El proyecto implementa un **router exequial** que clasifica las consultas entrantes en cuatro rutas de negocio y las gestiona con respuestas empáticas y éticas:

| Ruta | Significado |
|------|-------------|
| `necesidad_inmediata` | Consulta relacionada con una necesidad exequial actual o urgente. |
| `necesidad_futura` | Información preventiva o planificación anticipada. |
| `postventa` | Seguimiento de un servicio contratado, consultas posteriores o reclamos. |
| `generica` | Saludos y consultas ajenas al ámbito exequial. |
| `derivacion_humana` | Se propone atención de un asesor humano cuando la situación lo requiere. |

**Principios de comportamiento:** empatía, respeto, sin presión comercial, sin promesas no verificadas ni afirmaciones sobre precios, disponibilidad o coberturas no confirmadas.

**Arquitectura:**
- Router por reglas en español (clasificación sin consumo de tokens del modelo).
- Nodos independientes por ruta (`src/agente_exequial/graph.py`).
- API FastAPI con endpoints `POST /chat` y `POST /telegram`.
- Integración con Telegram mediante webhook y validación de secreto.
- Caché de contexto con Redis (fallback a memoria RAM).

---

## 2. Estructura del proyecto

```
proyecto-2-agentes-comerciales-exequial/
├── api/
│   ├── __init__.py
│   └── app.py                  # API FastAPI: POST /chat y POST /telegram
├── src/
│   ├── agente_exequial/
│   │   ├── __init__.py
│   │   ├── graph.py            # Grafo LangGraph del router
│   │   ├── prompts.py          # System prompts por nodo
│   │   └── tools.py            # Herramientas del agente
│   ├── agente_llamada/         # Agente original de recepción y triage
│   ├── agente_respuesta/       # Agente original de respuesta comercial
│   └── context_cache.py        # Caché Redis con fallback a memoria
├── tests/
│   ├── test_agente_exequial.py
│   ├── test_router_exequial.py
│   ├── test_api_chat.py
│   └── test_telegram.py
├── scripts/
│   └── telegram_webhook.py     # Configurar/verificar/eliminar webhook de Telegram
├── main.py                     # CLI: python main.py {agente} "mensaje"
├── requirements.txt
├── Procfile                    # Despliegue en Heroku
├── .env.example                # Plantilla de variables de entorno
└── README.md
```

---

## 3. Requisitos previos

- **Python 3.12** instalado en Windows.
- **Git** instalado.
- **Heroku CLI** (solo para despliegue en la nube).
- **Telegram** instalado en tu celular (solo para conectar el bot).

---

## 4. Cómo correr el router en local (CLI)

### Paso 1: Entrar a la carpeta del proyecto
```powershell
cd "C:\Users\abravos1970\Documents\Proyecto predeterminado\proyecto-2-agentes-comerciales-exequial"
```

### Paso 2: Activar el entorno virtual
```powershell
.venv\Scripts\Activate.ps1
```

### Paso 3: Ejecutar el agente por consola
```powershell
python main.py agente_exequial "Mi familiar falleció en el hospital, necesito servicio funerario urgente."
```

### Opciones adicionales
```powershell
# Ver los nodos visitados por el grafo
python main.py agente_exequial "Hola" --saltos

# Ver el diagrama Mermaid del grafo sin ejecutarlo
python main.py agente_exequial "Hola" --diagrama
```

---

## 5. Cómo levantar la API localmente

### Paso 1: Activar el entorno virtual
```powershell
.venv\Scripts\Activate.ps1
```

### Paso 2: Levantar el servidor FastAPI
```powershell
.venv\Scripts\uvicorn.exe api.app:app --reload --port 8000
```

Verás algo como:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Paso 3: Acceder a Swagger
Abre tu navegador en:
```
http://localhost:8000/docs
```

### Paso 4: Probar el endpoint POST /chat desde PowerShell

El endpoint `/chat` exige el token de acceso. Envíalo en la cabecera `Authorization`:
```powershell
$body = @{
    conversation_id = "prueba-001"
    message = "Mi familiar falleció en el hospital, necesito servicio funerario urgente."
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post `
  -Headers @{ Authorization = "Bearer TU_TOKEN_DE_PRUEBA" } `
  -ContentType "application/json" -Body $body
```

**Prueba de acceso (autorizado vs rechazado):**
```powershell
# Sin token -> 401 No autorizado
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post `
  -ContentType "application/json" -Body $body

# Con token -> 200 (respuesta real)
Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method Post `
  -Headers @{ Authorization = "Bearer TU_TOKEN_DE_PRUEBA" } `
  -ContentType "application/json" -Body $body
```

**Respuesta esperada:**
```json
{
  "ruta": "necesidad_inmediata",
  "motivo": "El mensaje menciona fallecimiento, deceso, hospital o necesidad de servicio inmediato.",
  "respuesta": "...texto empático del agente..."
}
```

---

## 6. Cómo correr las pruebas

```powershell
.venv\Scripts\Activate.ps1
.venv\Scripts\pytest.exe tests/ -v
```

**Resultado esperado:** 31 de 31 pruebas pasando.

| Archivo de pruebas | Cantidad | Qué verifica |
|--------------------|----------|--------------|
| `tests/test_agente_exequial.py` | 6 | Agentes originales, caché, blueprint |
| `tests/test_router_exequial.py` | 11 | Router, 4 rutas, derivación humana, casos ambiguos |
| `tests/test_api_chat.py` | 7 | Endpoint POST /chat, validaciones |
| `tests/test_telegram.py` | 7 | Endpoint POST /telegram, validación de secreto |

---

## 7. Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```powershell
Copy-Item .env.example .env
```

| Variable | Descripción |
|----------|-------------|
| `GOOGLE_API_KEY` | Clave de Google Generative AI (opcional en desarrollo, obligatoria con modelo real). |
| `MODELO` | Modelo de lenguaje por defecto (`gemini-3.5-flash-lite`). |
| `REDIS_URL` | URL de Redis (opcional; si no hay servidor, se usa memoria RAM). |
| `CACHE_TTL_SEGUNDOS` | Tiempo de vida del caché en segundos. |
| `API_TOKEN` | Token de acceso para `POST /chat` (cabecera `Authorization: Bearer <API_TOKEN>`). |
| `TELEGRAM_TOKEN` | Token del bot de Telegram (obtenido de @BotFather). |
| `TELEGRAM_SECRET` | Secreto para validar webhooks de Telegram (definido por ti). |
| `PUBLIC_URL` | URL pública del servicio (obligatoria en Heroku para el webhook). |

> **Seguridad:** Nunca subas el archivo `.env` con valores reales a GitHub. El `.gitignore` ya lo excluye.

---

## 8. Cómo desplegar en Heroku

### Paso 1: Instalar Heroku CLI
Descarga e instala Heroku CLI desde: https://devcenter.heroku.com/articles/heroku-cli

### Paso 2: Iniciar sesión
```powershell
heroku login
```

### Paso 3: Crear la aplicación en Heroku
```powershell
heroku create nombre-de-tu-app-exequial
```

### Paso 4: Configurar variables de entorno en Heroku
```powershell
heroku config:set GOOGLE_API_KEY="TU_CLAVE_REAL"
heroku config:set MODELO="gemini-3.5-flash-lite"
heroku config:set TELEGRAM_TOKEN="TU_TOKEN_REAL"
heroku config:set TELEGRAM_SECRET="TU_SECRETO_REAL"
heroku config:set PUBLIC_URL="https://nombre-de-tu-app-exequial.herokuapp.com"
```

### Paso 5: Subir el código
```powershell
git init
git add .
git commit -m "router + api + telegram"
git remote add origin https://github.com/agente-comercial-uai/agente-comercial-ecomerce.git
git branch -M main
git push -u origin main

git push heroku main
```

### Paso 6: Verificar que está operativo
```powershell
heroku open
```
Se abrirá `https://nombre-de-tu-app-exequial.herokuapp.com/docs` (Swagger en la nube).

---

## 9. Cómo conectar Telegram

### Paso 1: Crear un bot con BotFather
1. Abre Telegram en tu celular.
2. Busca **@BotFather**.
3. Envía `/newbot` y sigue los pasos.
4. Guarda el **token** que te da BotFather.

### Paso 2: Configurar las variables de entorno
En tu `.env` local o en Heroku (`heroku config:set`):
```
TELEGRAM_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_SECRET=MiSecretoTelegram123!
PUBLIC_URL=https://nombre-de-tu-app-exequial.herokuapp.com
```

### Paso 3: Configurar el webhook
Si estás en Heroku (URL pública):
```powershell
.venv\Scripts\Activate.ps1
.venv\Scripts\python.exe scripts/telegram_webhook.py set
```

Si estás probando localmente, usa **ngrok** para exponer tu laptop:
```powershell
ngrok http 8000
```
Copia la URL pública que te dé ngrok (ej. `https://abc123.ngrok-free.app`) y actualiza `PUBLIC_URL` antes de ejecutar el script de webhook.

### Paso 4: Verificar el webhook
```powershell
.venv\Scripts\python.exe scripts/telegram_webhook.py info
```

### Paso 5: Probar la conversación
1. Abre Telegram en tu celular.
2. Busca tu bot.
3. Envía un mensaje de texto.
4. El bot responderá con el texto empático generado por el agente exequial.

---

## 10. Seguridad y privacidad

- Los tokens y secretos **nunca** se escriben en el código fuente, prompts, registros ni Git.
- El archivo `.env` está en `.gitignore`.
- El endpoint `/chat` rechaza solicitudes sin un `Authorization: Bearer <API_TOKEN>` válido (HTTP 401).
- El endpoint `/telegram` rechaza solicitudes sin el encabezado `X-Telegram-Bot-Api-Secret-Token` válido (HTTP 401).
- Los datos de duelo y contacto son sensibles; el agente no los almacena permanentemente sin consentimiento explícito.
- No se exponen mensajes de error internos ni trazas al cliente externo.

---

## 10.b Límites conocidos

- Sin `GOOGLE_API_KEY`, el agente responde en **modo simulación** (aviso explícito `[modo simulación]`).
- El caché de contexto usa memoria RAM si no hay `REDIS_URL`; se pierde al reiniciar el proceso.
- `/chat` no conserva el historial entre peticiones (cada llamada es independiente).
- Si el proveedor del modelo falla, el endpoint responde `500` y lo registra en el log.
- El token de acceso y el secreto de Telegram deben estar en el entorno; una `API_TOKEN` ausente responde `503` (no configurado).

---

## 11. Solución de problemas comunes

| Error | Causa probable | Solución |
|-------|---------------|----------|
| `ModuleNotFoundError: No module named 'fastapi'` | Dependencias no instaladas | `.venv\Scripts\pip.exe install -r requirements.txt` |
| `401 No autorizado` en `/telegram` | `TELEGRAM_SECRET` incorrecto o falta encabezado | Verificar `.env` y encabezado `X-Telegram-Bot-Api-Secret-Token` |
| `422 Unprocessable Entity` en `/chat` | JSON mal formado o campo faltante | Enviar `conversation_id` y `message` con comillas rectas |
| `ngrok` no expone nada | ngrok no iniciado | Ejecutar `ngrok http 8000` en ventana separada |
| `git push heroku main` rechaza | No hay remote de Heroku | Ejecutar `heroku git:remote -a nombre-de-tu-app` |
| Swagger no carga | uvicorn no levantado | Ejecutar `.venv\Scripts\uvicorn.exe api.app:app --reload --port 8000` |

---

## 12. Licencia

Proyecto académico del curso de Orquestación Avanzada y Sistemas Multi-Agentes en Producción.
