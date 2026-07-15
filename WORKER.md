# Worker · drena la cola de Prewave y reconstruye

El worker es la mitad "IA" del sistema (la otra mitad, el botón + cola, es el PR #306 en Prewave).
Toma jobs de la tabla `agent_jobs`, reconstruye el carrusel y devuelve el resultado. **No vive en el
repo de Prewave** — corre como una sesión/agente de Claude con los MCP conectados.

## Prerrequisitos
1. **PR #306 mergeado** en Prewave (crea la tabla + endpoints `/agent-jobs`).
2. **`PIPELINE_API_KEY`**: ya está en prod (Secret Manager `pipeline-api-key`, proyecto prewave-prod). El worker la lee en su entorno desde el secret — NO hardcodear:
   `gcloud secrets versions access latest --secret=pipeline-api-key --project prewave-prod`
   y exportarla como `PIPELINE_API_KEY` en el entorno del worker (el `queue_client.py` la manda como `X-API-Key`). Verificado: GET /agent-jobs con la key → 200.
3. Al menos un **ADN pack `ready`** (`avatars/<slug>/adn.json` con templates) — ver `README.md`.
4. **MCP de Canva + Playwright** conectados en la sesión del worker. ⚠️ El de Canva se autentica vía
   claude.ai y su token caduca: pre-autenticar una vez y re-autenticar cada ~90 días o al fallar
   (ver `SPIKE-canva-api.md`). Por eso el v1 es **semi-persistente**, no 100% desatendido.

## Loop del worker
Por cada ciclo (a demanda, o agendado/`/loop`):

1. **Listar pendientes:** `python scripts/queue_client.py list`
   (→ `list_pending()`; usa `GET /agent-jobs?status=pending` con `X-API-Key`).
2. Por cada job `{id, design_request_id, reference_url, avatar_hint}`:
   a. **Reclamar:** `queue_client.claim(id)` (marca `processing`; evita que otro worker lo tome).
   b. **Resolver avatar:** matchear `avatar_hint` contra `prewave_program_match` de los ADN packs.
      Si el avatar no está `ready` → `fail(id, "avatar sin plantillas")` y seguir.
   c. **Reconstruir** siguiendo `AGENT.md` (Pasos 1–4) con **solo** `reference_url` como origen y el
      **ADN pack de ese avatar** (aislamiento). Descarga slides → visión → clasifica → copy-design del
      template del avatar → rellena en español con la voz del ADN → commit. Conservar datos EXACTOS.
   d. **Verificar** (paso 4b de AGENT.md / stage `verificar` del orquestador): comparar contra el referente.
   e. **Cerrar:** si pasa → `queue_client.complete(id, canva_edit_url)` (marca `done` + `result_url`;
      la tarjeta del board muestra "Ver 30x"). Si falla → `queue_client.fail(id, motivo)`.

## Formas de correr
- **A demanda (recomendado para v1):** en una sesión de Claude con los MCP, decir "drená la cola de carruseles".
  Claude corre el loop de arriba. Para tanda/paralelo usa `orchestrator.workflow.js` (fan-out reconstruir→verificar).
- **Agendado:** una Routine de Claude con Canva+Playwright pre-autenticados (ver caveat de token).
- **`orchestrator.workflow.js`**: el main loop arma los `jobs` (de `queue_client.list_pending()` + el ADN pack
  de cada avatar) y los pasa como `args`; el workflow hace el fan-out aislado. Tras cada job, el main loop
  llama `queue_client.complete/fail`.

## Aislamiento (recordatorio)
Cada job = un `reference_url` + un ADN pack. Nada compartido entre jobs. El worker nunca mezcla templates ni
marca de dos avatares. Ver `ORCHESTRATOR.md`.

## Estado
- `scripts/queue_client.py`: listo y probado (help/errores/import).
- Bloqueado para correr en vivo hasta: #306 mergeado + `PIPELINE_API_KEY` + ADN packs `ready` + Canva MCP autenticado.
