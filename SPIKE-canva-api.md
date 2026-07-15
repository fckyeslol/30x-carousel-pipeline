# Spike · ¿Qué permite la API de Canva desde un backend? (2026-07-09)

Pregunta: para productizar el agente como feature de Prewave (backend, no sesión de Claude),
¿se puede hacer la reconstrucción vía la **Connect API** pública de Canva?

## Lo que Prewave ya tiene (PR #161, `api/src/lib/canva.ts`)
- OAuth2 + PKCE por usuario. Scopes **solo lectura**: `design:content:read`, `design:meta:read`, `profile:read`.
- Endpoints usados: token, **exports** (crear job PNG + polling), `users/me/profile`.
- → Hoy Prewave solo **lee y exporta**. No crea, no rellena, no edita.

## Verdad de la Connect API (docs oficiales)
- **`design:content:write` = SOLO crear diseños nuevos** (blanco, preset, copia de brand template [preview],
  copia de diseño [preview], insertar assets de imagen). **NO existe endpoint para editar/reemplazar texto
  de elementos de un diseño existente.**
- La edición elemento-a-elemento que hicimos en el piloto (`start-editing-transaction` / `perform-editing-operations`
  con `replace_text`) es capacidad del **MCP/asistente de Canva**, NO de la Connect API pública. No es
  automatizable desde un backend.
- La **única** vía de "rellenar una plantilla con datos" por API = **Autofill API** (campos de datos: texto,
  imagen, charts) sobre **Brand Templates**.
- ⚠️ **Autofill + Brand Templates requieren Canva ENTERPRISE** (el token debe actuar en nombre de un miembro
  de una organización Canva Enterprise).

## Conclusión
Hay exactamente **dos caminos** para el feature en Prewave:

### Opción A — Autofill + Brand Templates (producto de verdad, backend puro)
- Requiere: **Canva Enterprise** + rearmar las plantillas por avatar como **Brand Templates con campos de
  autofill nombrados** (titular, cuerpo, stat, handle, slots de imagen…).
- Flujo backend: `get brand template dataset` → Claude API extrae el contenido del referente y lo mapea a los
  campos → `create design autofill job` → export/link → writeback al board.
- Ventajas: 100% backend, escalable, sin sesión de Claude en runtime; y **resuelve el problema de la piel
  equivocada** (los campos del template definen exactamente qué se rellena, sin bleed de otra marca).
- Costo: plan Enterprise + setup de cada template como brand template con data fields.
- Scopes nuevos en Prewave: `design:content:write` + `brandtemplate:content:read` (+ re-consentimiento).

### Opción B — Worker de Claude detrás del botón (sin Enterprise, reusa lo del piloto)
- El botón "Generar 30x" en la tarjeta **encola** el job; un **agente de Claude** (Claude Code / cloud agent)
  con el **MCP de Canva** lo drena (el `orchestrator.workflow.js` que ya construimos) y hace la
  reconstrucción como en el piloto (copy-design + replace_text).
- Ventajas: no necesita Enterprise; reusa TODO lo construido; funciona ya.
- Costo/caveat: el "backend" es en realidad un worker de Claude con MCP; el MCP de Canva está autenticado vía
  claude.ai → hay que resolver auth en el worker (no es un servicio REST puro). Menos "producto", más "robot".

## DECISIÓN (2026-07-09): **Opción B** (sin Canva Enterprise)
El usuario descartó Enterprise → vamos con el **worker de Claude + MCP detrás del botón** en Prewave.
Reusa el piloto (copy-design + replace_text vía MCP) y el `orchestrator.workflow.js`.

### Arquitectura Opción B
1. **Prewave (PR, parte fácil y determinista):** botón "Generar 30x" en la tarjeta de `/design-requests`
   → escribe en una tabla/cola `agent_jobs` (request_id, referente_ig, avatar, estado=pending). Endpoint
   para listar pending + marcar done. Sin lógica de IA en el backend.
2. **Worker de Claude (donde vive la IA + los MCP):** una sesión/agente de Claude con **Canva MCP +
   Playwright** conectados, que drena la cola: por cada job corre el flujo del piloto (AGENT.md) con el
   ADN pack del avatar y hace `deliver` del borrador al board.
3. Diseñadora: aprieta el botón, y minutos después ve el borrador en la tarjeta para revisar/aprobar.

### ⚠️ El riesgo a validar PRIMERO (worker ↔ auth del MCP de Canva)
El MCP de Canva se autentica vía claude.ai (login interactivo). Para que el worker corra **desatendido**
hay que confirmar que esa conexión persiste en un Claude Code agendado/headless. Si NO persiste, el v1
realista es: la cola existe en Prewave, y un **worker semi-persistente** (sesión de Claude donde el MCP
quedó logueado, o disparo manual/periódico) la drena. Menos "mágico", igual de útil (autoservicio vía el
board + IA por detrás). **Este spike de auth es el siguiente paso técnico.**

## Resultado del spike de auth (2026-07-09, docs Claude Code oficiales)
- Los conectores de claude.ai (Canva) **se heredan en Routines agendadas** SI un humano los autenticó antes,
  PERO el token caduca (~OAuth típico) y **en cloud desatendido no hay recuperación automática documentada**:
  si expira, la herramienta simplemente deja de estar disponible, en silencio. Claude Code docs: una sesión
  desatendida que sobrevive al login "stops making progress once the credential expires and can't recover
  until you sign in again."
- La alternativa "self-host MCP de Canva con credenciales de app" da auth estable PERO ese MCP correría sobre
  la **Connect API pública, que NO tiene edición de texto** (lo confirmamos) → no sirve para nuestro flujo.
- La edición (`replace_text`) SOLO existe en el conector Canva de claude.ai → que es justo el de auth frágil.

### CONCLUSIÓN: no hay worker 100% desatendido sin Enterprise.
**v1 realista = cola en Prewave + worker SEMI-persistente:** un humano pre-autentica el conector Canva una
vez; el worker (Routine agendada o sesión viva) drena la cola; se monitorea y se **re-autentica cada ~90 días
o cuando falle**. La experiencia de la diseñadora no cambia (botón → borrador → revisa); lo único no-cero-touch
es la re-auth periódica del worker. Fuentes: code.claude.com/docs/en/routines, /authentication, /mcp.

## Fuentes
- Scopes: https://www.canva.dev/docs/connect/appendix/scopes/
- Create design: https://www.canva.dev/docs/connect/api-reference/designs/create-design/
- Autofill guide: https://www.canva.dev/docs/connect/autofill-guide/
- Autofill (enterprise req): https://www.canva.dev/docs/connect/api-reference/autofills/create-design-autofill-job/
- Brand template dataset: https://www.canva.dev/docs/connect/api-reference/brand-templates/get-brand-template-dataset/
