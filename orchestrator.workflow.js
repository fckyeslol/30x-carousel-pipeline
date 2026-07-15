export const meta = {
  name: '30x-carousel-orchestrator',
  description: 'Fan-out de workers aislados: reconstruye carruseles 30x por avatar desde referentes IG y verifica antes de entregar',
  phases: [
    { title: 'Reconstruir' },
    { title: 'Verificar' },
  ],
}

// ─────────────────────────────────────────────────────────────────────────────
// Orquestador de carruseles 30x — workers en paralelo + aislamiento.
//
// Los scripts de Workflow NO leen disco ni MCP config, así que el MAIN LOOP
// (Claude interactivo) prepara los jobs y los pasa como `args`:
//
//   args = {
//     deliver: false,                 // true = entregar borrador al board (deliver); false = solo construir y reportar
//     jobs: [{
//       request_id:  "<uuid design-request>",
//       referente_ig:"https://www.instagram.com/p/XXXX/",
//       avatar_slug: "andres",
//       adn:         { ...contenido de avatars/andres/adn.json... }   // el pack COMPLETO, inline (aislamiento)
//     }, ...]
//   }
//
// CONTRATO DE AISLAMIENTO: cada agent() recibe EXACTAMENTE un job = un referente + un ADN pack.
// No hay estado compartido; un worker no puede ver el referente ni el pack de otro avatar.
//
// ⚠️ MCP: los subagentes necesitan Canva + Playwright. El MCP de Canva está autenticado vía
// claude.ai y puede faltar en corridas headless/cron → correr en sesión interactiva.
// ─────────────────────────────────────────────────────────────────────────────

const RECONSTRUCT_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['request_id', 'ok', 'canva_edit_url', 'slides_built', 'notes'],
  properties: {
    request_id:   { type: 'string' },
    ok:           { type: 'boolean' },
    canva_edit_url:{ type: 'string' },
    slides_built: { type: 'integer' },
    notes:        { type: 'string' },
  },
}

const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['request_id', 'passes', 'issues'],
  properties: {
    request_id: { type: 'string' },
    passes:     { type: 'boolean' },       // true = fiel al referente, marca correcta, sin invenciones
    issues:     { type: 'array', items: { type: 'string' } },
  },
}

const jobs = (args && args.jobs) || []
const deliver = !!(args && args.deliver)

if (!jobs.length) {
  log('No hay jobs. Pasar args.jobs (ver cabecera del script).')
  return { processed: 0 }
}
log(`${jobs.length} carrusel(es) en cola. deliver=${deliver}`)

// Pipeline por job: reconstruir → verificar. Sin barrera: cada job avanza independiente.
const results = await pipeline(
  jobs,
  // Stage 1 — worker de reconstruccion (aislado a ESTE job + su ADN pack)
  (job) => agent(
    [
      'Sos un worker de reconstrucción de carruseles 30x. Seguí el procedimiento de AGENT.md.',
      'AISLAMIENTO: trabajás SOLO con este referente y este ADN pack. No inventes nada; solo transponé.',
      `request_id: ${job.request_id}`,
      `referente_ig: ${job.referente_ig}`,
      `avatar: ${job.avatar_slug}`,
      `ADN pack (marca, voz, templates 30x del avatar):`,
      JSON.stringify(job.adn),
      'Pasos: descargá las slides del referente (Playwright + carousel_media), leélas con visión,',
      'clasificá cada una a un layout, duplicá el template del avatar (copy-design) del tipo que corresponda,',
      'rellená por rol de campo en español con la voz del ADN, commit. Conservá cifras/datos EXACTOS del referente.',
      'Devolvé el canva_edit_url, cuántas slides armaste y notas (incluí si algo no calzó).',
    ].join('\n'),
    { label: `build:${job.avatar_slug}:${job.request_id.slice(0,8)}`, phase: 'Reconstruir', schema: RECONSTRUCT_SCHEMA }
  ),
  // Stage 2 — verificador (anti-alucinación): compara la reconstrucción contra el referente
  (built, job) => {
    if (!built || !built.ok) return { request_id: job.request_id, passes: false, issues: ['reconstrucción falló'] , built }
    return agent(
      [
        'Sos el verificador anti-alucinación. Compará el carrusel reconstruido contra el referente original.',
        `referente_ig: ${job.referente_ig}`,
        `canva a revisar: ${built.canva_edit_url}`,
        `marca esperada del avatar: handle=${job.adn?.brand?.handle} tagline="${job.adn?.brand?.tagline}"`,
        'Chequeá: (1) cada cifra/dato del referente sobrevive EXACTO; (2) no se inventaron datos ni fuentes;',
        '(3) la marca/voz es la del avatar (no de otro); (4) cada slide del referente quedó representada.',
        'passes=true solo si todo se cumple. Listá issues concretos si no.',
      ].join('\n'),
      { label: `verify:${job.avatar_slug}:${job.request_id.slice(0,8)}`, phase: 'Verificar', schema: VERIFY_SCHEMA }
    ).then(v => ({ ...v, built }))
  }
)

const clean = results.filter(Boolean)
const passed = clean.filter(r => r.passes)
const failed = clean.filter(r => !r.passes)
log(`Verificados OK: ${passed.length}/${clean.length}. Con issues: ${failed.length}.`)

// Entrega (opcional): solo los que pasaron el verificador. El deliver real lo hace el main loop
// (POST /design-requests/:id/deliver) porque necesita el token/MCP de la sesión.
return {
  processed: clean.length,
  deliverables: passed.map(r => ({ request_id: r.request_id, canva_edit_url: r.built.canva_edit_url })),
  needs_review: failed.map(r => ({ request_id: r.request_id, issues: r.issues })),
  deliver_requested: deliver,
}
