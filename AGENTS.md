# AGENTS.md · proyecto-2-agentes-comerciales-exequial

Proyecto del sector exequial (funerario). Dos agentes:

1. **`src/agente_llamada/`** · agente de recepción y triage de llamadas 24/7.
   Recopila datos, valida urgencia y contiene emocionalmente. No cierra ventas.
2. **`src/agente_respuesta/`** · agente de respuesta comercial sensible, empática y persuasiva.
   Elabora cotizaciones, presenta planes y guía la decisión comercial con visión prospectiva.

## Arquitectura
- Blueprint: `blueprint.json` y `blueprint.mmd` (diseño del grafo).
- Context caching: Redis con fallback a memoria (`context_cache.py`).
- Fallback: modo simulación sin `GOOGLE_API_KEY` y respuesta de texto ante fallo de API.

## Ejecución
`python main.py {nombre_agente} "mensaje"` donde `{nombre_agente}` es `agente_llamada` o `agente_respuesta`.
- `--saltos`: imprime nodos visitados.
- --diagrama: imprime Mermaid del grafo sin ejecutar.

## Variables de entorno
- `GOOGLE_API_KEY`: clave de Google Generative AI (opcional; sin ella modo simulación).
- `MODELO`: modelo por defecto `gemini-3.5-flash-lite`.
- `REDIS_URL`: opcional. Si no hay servidor Redis, se usa caché en memoria.
- Claves solo en `.env` (ignorado). `.env.example` lista las variables.
