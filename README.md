# Pipeline de Carruseles 30x — sistema multi-avatar

Agente que toma un **referente de Instagram** (desde el board de Diseño de Prewave) y lo **reconstruye
en el formato 30x del avatar** que corresponde, entregando un borrador para revisión humana.
**1 lógica, muchos avatares** (ADN packs), workers en paralelo, aislamiento anti-alucinación.

## Archivos

| Archivo | Qué es |
|---|---|
| `AGENT.md` | La lógica del agente (flujo de 1 carrusel, paso a paso) |
| `ORCHESTRATOR.md` | Diseño del fan-out + contrato de aislamiento |
| `registry.json` | Layouts, masters, intake de Prewave, límites conocidos |
| `layouts-library.md` | Catálogo de los 10 layouts 30x |
| `avatars/<slug>/adn.json` | **ADN pack por avatar** = marca + voz + templates 30x. La config que varía por avatar |
| `avatars/_TEMPLATE/adn.json` | Blueprint para un avatar nuevo |
| `orchestrator.workflow.js` | Script ejecutable del fan-out (herramienta Workflow) |
| `scripts/new_avatar.py` | Crea el ADN pack de un avatar nuevo |
| `scripts/check_packs.py` | Reporta qué avatares están READY vs faltan plantillas |
| `scripts/decode_slides.py` | Helper: decodifica las slides descargadas del referente |

## RUNBOOK — cuando lleguen las plantillas

Por cada avatar:

1. **Crear el pack** (si no existe):
   ```
   python scripts/new_avatar.py "Nombre Avatar" --handle @handle --tagline "..." --voice tuteo
   ```
2. **Pegar los `design_id`** de sus plantillas 30x en `avatars/<slug>/adn.json → templates`
   (por tipo de lámina: cover, data, comparative, single_tip, principle, process, insight, cta).
   Cada tipo puede tener `slot_pages` (páginas repetibles del molde).
3. **Marcar listo:** poner `"status": "ready"`.
4. **Verificar:**
   ```
   python scripts/check_packs.py      # debe salir el avatar como READY
   ```

Cuando haya ≥1 avatar READY, correr el orquestador (sesión interactiva con Canva + Playwright):
- El main loop lee `/design-requests`, arma los `jobs` (request + referente + ADN pack del avatar READY),
  e invoca `orchestrator.workflow.js` con esos `jobs` → fan-out reconstruir→verificar → entrega borradores.

## Garantías anti-alucinación (por diseño)

- Cada worker ve **solo** su referente + su ADN pack (aislamiento).
- **Solo transpone**: cifras/datos del referente exactos; nada inventado.
- Un avatar sin plantillas (`draft`) **se salta** — nunca sale con piel equivocada.
- **Verificador** compara la salida vs el referente antes de entregar.
- **Revisión humana**: se entrega como borrador → la revisora aprueba.

## Estado

- Arquitectura y scaffold: **listos**.
- `avatars/andres`: pack creado (solo `comparative` con template; resto pendiente) → `draft`.
- Pendiente para encender: **recibir las plantillas por avatar** → pasos del runbook.
