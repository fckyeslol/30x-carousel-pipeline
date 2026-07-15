# Orquestador · workers en paralelo + aislamiento

> Escala el agente de un carrusel a **muchos referentes de muchos avatares**, con **1 sola lógica**
> (`AGENT.md`) parametrizada por avatar (`avatars/<slug>/adn.json`). Multi-agente = **workers paralelos
> del mismo agente**, NO N lógicas distintas. Ver también `registry.json`, `layouts-library.md`.

## Modelo mental

```
                       ┌─ worker(job) ─ solo referente A + ADN avatar A ─┐
GET /design-requests ──┼─ worker(job) ─ solo referente B + ADN avatar B ─┼─→ deliver borradores
   (cola de refs IG)   └─ worker(job) ─ solo referente C + ADN avatar A ─┘   (revisión humana)
        │                        ▲
        └── agrupar por avatar ──┘ (saltar avatares con ADN pack status != 'ready')
```

- **1 agente** (AGENT.md) = 1 lógica. **N workers** = N *instancias* del mismo agente corriendo en paralelo.
- Lo único que varía por worker: **qué job** (referente) y **qué ADN pack** carga.

## Contrato de AISLAMIENTO (anti-alucinación) — invariante

Cada worker procesa **exactamente un job** y ve **solo**:
1. **Un referente** (las slides de UN post de IG). No otros posts, no el grid del perfil.
2. **Un ADN pack** (`avatars/<slug>/adn.json` del avatar dueño de ese request). No los packs de otros avatares.

Prohibido entre workers: estado compartido, mezclar templates/marca de dos avatares, reusar contenido de otro referente. Esto es lo que hace **imposible** el bug del piloto (marca de Multipliers en un carrusel de Andrés): un worker de Andrés no tiene acceso al pack de Multipliers.

Reglas de contenido dentro del worker (de `voice_dna`):
- **Solo transponer:** el texto sale del referente; la marca/voz sale del ADN pack; **nada más se inventa**.
- Cifras, datos y fuentes del referente se conservan **exactos**. Si el referente no trae fuente, no se fabrica.
- Cada slide del referente debe caer en un layout (`classifier_rules`); si no clasifica, se marca — no se fuerza.

## Flujo del orquestador

1. **Cargar ADN packs:** leer `avatars/*/adn.json`. Considerar solo los `status == "ready"`.
   (Un avatar sin plantillas entregadas queda en `draft` y se SALTA — no se procesa con piel equivocada.)
2. **Leer la cola:** `GET /design-requests` (ver `prewave_intake`). Filtrar actionables: referencia
   `instagram.com/(p|reel)/` + status `solicitado|en_diseno` + sin `deliverable_url`.
3. **Resolver avatar de cada request:** por `programs`/`objective` contra `prewave_program_match` de cada pack.
   Requests cuyo avatar no está `ready` → se dejan en la cola (no se tocan).
4. **Fan-out:** disparar **un worker por request** en paralelo (concurrencia acotada). Cada worker:
   `carga ADN pack del avatar → ejecuta AGENT.md Pasos 1–4 con ESE referente y ESOS templates`.
5. **Verificador (2º paso por job):** un agente compara la reconstrucción contra el referente
   (¿sobrevivió cada dato? ¿se inventó algo? ¿marca correcta del avatar?). Si falla → no entrega, marca para revisión.
6. **Writeback:** `deliver` como borrador → `revisión` → aprueba la revisora. (Ver `prewave_intake.writeback`.)

## Mecanismo de ejecución

- **Preferido (fan-out real):** la herramienta **Workflow** (pipeline/parallel) — un stage `reconstruir` y un
  stage `verificar` por job; concurrencia automática. Cada `agent()` = un worker aislado.
- **⚠️ Caveat MCP:** el MCP de **Canva** está autenticado vía claude.ai; en corridas *headless/cron* puede no
  estar disponible en los subagentes. Hoy correr el orquestador en una **sesión interactiva** con Canva +
  Playwright conectados (o usar el token de `prewave_token` del navegador, como en el piloto). Playwright es local.
- **Fallback:** loop secuencial sobre la cola (mismo agente, un job a la vez) — más lento, sin dependencia de subagentes.

## Onboarding de un avatar nuevo (la escalabilidad)

Llega un ADN + plantillas nuevas → 
1. `cp -r avatars/_TEMPLATE avatars/<slug>` y rellenar `adn.json` (brand + voice_dna + `prewave_program_match`).
2. Pegar los `design_id` de sus plantillas 30x por tipo de lámina.
3. Poner `status: "ready"`.
4. Listo — el orquestador ya lo incluye en la cola. **Cero código nuevo.**

## Estado actual

- Andrés: pack creado, solo `comparative` tiene template (los demás pendientes de sus plantillas) → sigue `draft`.
- Resto de avatares: pendientes de recibir sus plantillas (lo que van a compartir) → crear un pack por avatar.
- Verificador: diseñado aquí; falta cablearlo como stage cuando corramos el fan-out.
