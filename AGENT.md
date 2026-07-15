# Agente · Carrusel 30x

> **Qué hace:** dado un referente (carrusel de Instagram o TikTok), lo **replica con el ADN de un avatar**.
> La **referencia es el molde**: de ahí sale la estructura. El **ADN es la máquina**: tipografía, paleta,
> identidad y voz. El output es *ese* carrusel, hablado y vestido por *ese* avatar.
>
> **Cómo se ejecuta:** este documento es el procedimiento que sigue Claude Code (con el **MCP de Canva** y el
> **MCP de Playwright** conectados). Humano-en-el-loop al final: la diseñadora aprueba.
> Referencia: [`avatars/<slug>/adn.json`](./avatars) (la máquina) y [`ORCHESTRATOR.md`](./ORCHESTRATOR.md) (aislamiento).

## El modelo (leer esto antes que nada)

```
   REFERENTE  ──►  estructura  ──┐
   (el molde)                    ├──►  CARRUSEL 30x
   ADN del avatar ──► identidad ─┘     (la referencia, con el ADN nuevo)
   (la máquina)
```

**No hay catálogo de layouts del que elegir.** No se clasifica el referente contra una lista de moldes
predefinidos: se **lee su estructura y se replica**. Si el referente tiene 7 láminas con un dato grande
arriba y un pie de página, eso es lo que se construye — con la tipografía y los colores del avatar.

`layouts-library.md` sobrevive solo como **vocabulario descriptivo** (para nombrar lo que se ve en un
referente), **no** como catálogo de selección. Cualquier estructura nueva es válida por definición.

---

## Requisitos previos
- MCP de **Canva** conectado a la cuenta **30x** (verificar: "lista mis diseños" debe mostrar contenido 30x, no personal).
- MCP de **Playwright** con sesión de Instagram (para descargar slides).
- Python disponible (para decodificar imágenes).
- El avatar destino con `status: "ready"` en su `adn.json` (ADN completo + lienzo creado).

---

## Paso 0 — Intake

Del board de Diseño (`/design-requests`) o de la cola `agent_jobs`. Ver `registry.json → prewave_intake`.
1. Autenticarse: `Authorization: Bearer <token>` (login o cookie `prewave_token`).
2. Tomar la solicitud → extraer `request_id`, `referente_url`, `title`, `objective`, `programs`.
3. **Resolver el avatar y cargar SU ADN pack** (`avatars/<slug>/adn.json`) matcheando `programs`/`objective`
   contra `prewave_program_match`. Si no está `ready` → dejar en cola, no procesar.
4. A partir de acá: **solo** el referente como fuente de contenido y **solo** ese ADN como identidad.
   Nada de otro avatar. Ver contrato de aislamiento en `ORCHESTRATOR.md`.

## Paso 1 — Descargar las slides del referente

1. `browser_navigate` a la URL del post (`https://www.instagram.com/p/<code>/`).
2. Extraer las URLs reales del **JSON embebido, NO del DOM**:
   `browser_evaluate` → en `script[type="application/json"]` buscar `carousel_media[]`,
   tomar por slide el candidato de mayor `width` en `image_versions2.candidates`.
   - ⚠️ **No scrapear `<img>` del DOM**: agarra miniaturas de OTROS posts del perfil (bug real ya visto).
3. Descargar **dentro** del navegador (las URLs del CDN dan **403** fuera de la sesión):
   `browser_evaluate` con `fetch` → `blob` → `readAsDataURL` → array base64, guardado con `filename`.
4. Decodificar: `python scripts/decode_slides.py <json> <carpeta-salida>`.

## Paso 2 — Leer la estructura del referente (el molde)

5. Leer cada slide con **visión** (Read sobre cada PNG).
6. Por lámina, describir su **estructura**, no su categoría:
   - qué bloques de texto hay y en qué orden vertical
   - la **jerarquía** (qué domina: un número gigante, un titular, una lista)
   - el **rol** de cada bloque (gancho, dato, contraste, paso, cita, cierre…)
   - qué está **enfatizado** y cómo (tamaño, color, peso)
7. Resultado: una **especificación de estructura** por lámina. Ese es el molde. Se respeta el conteo de
   láminas del referente salvo que haya un motivo explícito.

## Paso 3 — Pasar la estructura por el ADN (la máquina)

8. Reescribir el contenido en **español**, con la **voz** del avatar (`voice_dna`, `brand`).
   - ⚠️ **Fidelidad estricta:** cada cifra, dato y fuente del referente sobrevive **exacto**.
     No se inventa nada. Si el referente no lo dice, no existe.
9. Asignar la **identidad visual** (`visual_identity`): cada bloque recibe tipografía, cuerpo, color y
   posición según su rol y la jerarquía observada. La estructura es del referente; los valores son del ADN.
10. Cerrar con la **firma** del avatar (`visual_identity.firma`).

## Paso 4 — Materializar en Canva

> **Por qué existe el "lienzo de ADN"** — límite duro de la plataforma, no una decisión de diseño:
> la API de Canva **no tiene operación para crear texto** (`insert_fill` solo acepta imagen/video),
> y `format_text` **no cambia la familia tipográfica**. Un texto en Instrument Serif solo puede **nacer**
> así, vía import de HTML. Por eso cada avatar tiene **un lienzo**: un diseño con su fuente y su fondo ya
> horneados y una **reserva de bloques de texto vacíos**. El lienzo **no aporta layout** — es materia prima
> tipográfica. Toda la estructura sigue viniendo del referente.

11. `copy-design` del lienzo del avatar (`adn.json → canvas.design_id`), subseteando a la cantidad de
    láminas del referente. ⚠️ La API **no duplica páginas**: el lienzo debe tener suficientes.
12. `start-editing-transaction` sobre la copia → devuelve `element_id` frescos (cambian en cada copia).
13. `perform-editing-operations` en bulk, esculpiendo cada lámina contra la spec del Paso 3:
    - `replace_text` → el contenido
    - `format_text` → cuerpo, color, peso, itálica, alineación, interlineado (**familia no**, ya viene del lienzo)
    - `position_element` / `resize_element` → la maqueta observada en el referente
    - `delete_element` → los bloques de reserva que no se usaron
14. `commit-editing-transaction`. **Sin commit, los cambios se pierden.**

## Paso 5 — Verificar y entregar

15. **Verificar contra el referente antes de entregar:** ¿cada dato/cifra sobrevivió exacto? ¿no se inventó
    nada? ¿la estructura es la del referente? ¿la identidad es la del avatar correcto? Si falla, no entregar.
16. **Writeback:** `POST /production/:brief_id/design` con `{ driveUrl: <edit_url>, notes: "borrador
    generado por agente — revisar", editorId: <diseñadora> }` → queda en "por editar" para aprobación.

---

## Crear el lienzo de un avatar (una vez por ADN)

No requiere diseñadora. Ver `scripts/build_canvas.py` y `CANVAS.md`:
1. Generar el HTML del lienzo desde `adn.json` (fuente embebida, fondo, N páginas × M bloques).
2. Publicarlo en el repo (público) → `import-design-from-url` con la URL cruda.
3. `resize-design` a 1080×1350.
4. Pegar el `design_id` en `adn.json → canvas` y poner `status: "ready"`.

## Reglas de oro
- **La referencia manda la estructura; el ADN manda la identidad.** Nunca al revés.
- **No inventar datos.** Cifras y fuentes salen del referente, exactas, o no salen.
- **Un avatar por vez.** Nunca mezclar identidades (ver `ORCHESTRATOR.md`).
- **Cuenta correcta primero.** Si aparece contenido personal, reconectar el conector a 30x.
- **Estructura rara ≠ estructura inválida.** Si el referente hace algo que no vimos antes, se replica igual.

## Estado / pendientes
- Los lienzos de Cinthya y Guillermo: **por crear** (mecanismo validado, ver `CANVAS.md`).
- El fondo del lienzo requiere **un ajuste manual único** al crearlo (el import no trae `background-color`).
- Referentes de **TikTok**: el Paso 1 está escrito para IG; falta el extractor equivalente.
