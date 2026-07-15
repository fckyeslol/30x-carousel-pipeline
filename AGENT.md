# Agente · Carrusel 30x desde Instagram

> **Qué hace:** dado uno o más links de Instagram (carruseles de referentes), reconstruye cada uno como
> un carrusel con el **formato 30x** en Canva y entrega el link editable para que el diseñador apruebe.
>
> **Cómo se ejecuta:** este documento es el procedimiento que sigue Claude Code (con el **MCP de Canva** y el
> **MCP de Playwright** conectados). Es un agente *humano-en-el-loop* en el paso final: el diseñador aprueba.
> Referencia: [`registry.json`](./registry.json) (masters, layouts, reglas) y [`layouts-library.md`](./layouts-library.md) (detalle).

## Requisitos previos
- MCP de **Canva** conectado a la cuenta **30x** (verificar: "lista mis diseños" debe mostrar contenido 30x, no personal).
- MCP de **Playwright** con sesión de Instagram del usuario (para descargar slides).
- Python disponible (para decodificar imágenes).

---

## Paso 0 — Intake: solicitudes de carrusel en el board de DISEÑO (fuente por defecto)

El agente se alimenta del **board de Diseño** (`/design-requests`), donde las solicitudes traen la **referencia de IG directa**. Ver `registry.json → prewave_intake`.
1. Autenticarse: `Authorization: Bearer <token>` (login o cookie `prewave_token` de sesión web).
2. `GET /design-requests` → filtrar la cola del agente: `asset_types` incluye "carrusel" **y** `reference_urls` tiene link `instagram.com/(p|reel)/` **y** `status ∈ {solicitado, en_diseno}` **y** sin `deliverable_url`.
3. Por cada solicitud, extraer (ver `field_map`): `request_id`, `referente_ig`, `title`, `objective`, `programs`, `assigned_designer_id`.
4. **Resolver el avatar y cargar SU ADN pack** (`avatars/<slug>/adn.json`) matcheando `programs`/`objective` contra `prewave_program_match`. Si el avatar no está `status:"ready"` (plantillas incompletas) → NO procesar, dejar en cola. Reconstruir (Pasos 1–4) usando **solo** `referente_ig` como origen de contenido y **los templates + brand + voice_dna de ESE ADN pack** (nada de otro avatar). Ver contrato de aislamiento en `ORCHESTRATOR.md`.
4b. **Verificar antes de entregar:** comparar la reconstrucción contra el referente — ¿cada dato/cifra sobrevivió exacto?, ¿no se inventó nada?, ¿marca/voz del avatar correcta? Si falla, no entregar; marcar para revisión.
5. Writeback (ver `writeback`): si la solicitud está en `solicitado`, primero aceptar/autoasignar; luego `POST /design-requests/:id/deliver` con el `edit_url` de Canva y nota "borrador generado por agente - revisar" → pasa a `revision` para que Isabella apruebe.

## Procedimiento (por cada carrusel)

### Paso 1 — Descargar las slides del referente (si no vinieron en media_urls)
1. `mcp__playwright__browser_navigate` a la URL del post (`https://www.instagram.com/p/<code>/`).
2. Extraer las URLs reales del carrusel del **JSON embebido**, NO del DOM:
   `browser_evaluate` → buscar en `script[type="application/json"]` la clave `carousel_media[]`,
   tomar por slide el candidato de mayor `width` en `image_versions2.candidates`.
   - ⚠️ **No scrapear `<img>` del DOM**: agarra miniaturas de OTROS posts del perfil (bug real ya visto).
3. Descargar dentro del navegador (las URLs del CDN dan **403** fuera de la sesión):
   `browser_evaluate` con `fetch` → `blob` → `FileReader.readAsDataURL` → devolver array base64,
   guardándolo con el parámetro `filename` (queda en el working dir, no en el scratchpad).
4. Decodificar a imágenes: `python scripts/decode_slides.py <ruta-del-json> <carpeta-salida>`.

### Paso 2 — Extraer y clasificar el contenido
5. Leer cada slide con **visión** (herramienta Read sobre cada PNG) — no hace falta OCR aparte.
6. Por slide, capturar: texto + **rol** (hook, dato, comparación, tip, proceso, cita, CTA…).
7. Mapear cada slide a un `layout` usando `classifier_rules` de `registry.json`.
   Resultado = una secuencia de layouts, p. ej. `[L1_cover, L3, L3, L6, L6, L9_insight, L8_cta]`.

### Paso 3 — Elegir master y longitud
8. El **tipo dominante** de cuerpo decide el master:
   - mayoría comparativos → `comparative` (máx 5 slots)
   - mayoría tips de un bloque → `single_tip` (hasta 13)
   - mayoría datos → `data`; mixto corto → `multipliers_kit`; editorial con foto → `editorial_image`; evento → `event`.
9. Calcular `page_numbers` = `[cover] + [N slot_pages] + [cta]` subseteando el master.
   - ⚠️ **No exceder `max_slots`**. Si el referente trae más cuerpos, **condensar** (elegir los más fuertes) —
     la API **no puede duplicar páginas**.

### Paso 4 — Construir en Canva
10. `mcp__canva__copy-design` con `design_id` del master + `page_numbers` calculados → copia limpia.
11. `mcp__canva__start-editing-transaction` sobre la copia → devuelve la estructura con `element_id` frescos.
12. **Mapear roles → element_id** por el texto/posición de cada lámina (los IDs cambian por copia).
13. Redactar el contenido en **español**, aplicando `brand_config_by_program` (handle/tagline/CTA/voz del programa objetivo).
14. `mcp__canva__perform-editing-operations` en bulk (`replace_text`, y `update_fill` para imágenes en L7).
    - ⚠️ Resaltado por-palabra se pierde con `replace_text` (ver `known_limits`).
15. `mcp__canva__commit-editing-transaction`. **Sin commit los cambios se pierden.**

### Paso 5 — Verificar y entregar (writeback = borrador en la tarjeta)
16. `mcp__canva__get-design-pages` para revisar (⚠️ el `fallback` S3 puede venir cacheado; fuente de verdad = `edit_url`).
17. **Escribir de vuelta en Prewave:** `POST /production/:brief_id/design` con
    `{ driveUrl: <edit_url de Canva>, notes: "borrador generado por agente — revisar", editorId: <diseñadora del avatar> }`.
    → queda en `design_drive_url` de la tarjeta y pasa a **"por editar"**; la diseñadora ajusta y aprueba.
    Requiere token con rol diseñador/admin y que la tarjeta esté en `por_disenar`.

## Disparo — "al aceptar en el Tinder"
El agente es Claude + MCPs; **no** corre dentro del backend de Prewave. Por eso "al aceptar" se implementa en 2 fases:
- **Fase 1 (sin tocar Prewave, para validar ya):** el runner drena la cola implícita — `GET /production/` filtrado a carruseles con `design_drive_url == null`; los recién aceptados aparecen ahí. Se corre a demanda o en loop frecuente.
- **Fase 2 (evento real, requiere PR en Prewave):** en el branch de carrusel de `enteringProduction` (`api/src/routers/briefs.ts` ~750) encolar el brief al aceptar (flag/tabla `agent_jobs`); un **Claude cloud agent** (skill `schedule`) drena la cola y corre este procedimiento.

---

## Reglas de oro (aprendidas en producción)
- **Cuenta correcta primero.** Si aparece contenido personal (Sembradores, Moriah), la cuenta está mal; reconectar el conector a 30x.
- **Condensar > forzar.** Mejor 5 tips fuertes bien puestos que 8 mal encajados en un molde que no da.
- **Marca consistente.** Aplicar SIEMPRE el `brand_config_by_program`; no heredar el handle/tagline del master de origen (la cuenta los tiene mezclados).
- **No inventar layouts.** Si un slide no calza en ningún layout del registry, marcarlo y proponer un layout nuevo — no deformar el contenido.

## Estado / pendientes
- `brand_config_by_program` tiene valores **observados, no confirmados** → el usuario debe fijar los canónicos.
- Master `comparative` tope 5 slots; si se necesitan más de forma recurrente, un humano crea una vez en Canva un master comparativo de 8 slots (la API no puede).
- `L7_editorial` con reemplazo de imagen (`update_fill`) aún no probado end-to-end.
