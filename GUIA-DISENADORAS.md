# Guía · Generar carruseles 30x con IA (para diseñadoras)

## ¿Qué es esto?

En el board de **Diseño** (`prewave.oracle30x.co/diseno`), las solicitudes que traen un **referente de Instagram**
tienen un botón **"Generar 30x"**. Al apretarlo, una IA baja ese carrusel de referencia, lo reconstruye con el
formato 30x y te deja un **borrador en Canva** listo para que lo ajustes y lo apruebes.

**Importante:** la IA no genera sola en la nube. Corre un "**worker**" **en tu computadora**. Si tu worker no está
prendido, el trabajo queda encolado esperando. Por eso esta guía: dejar tu worker listo y prendido.

---

## PARTE 1 · Setup (una sola vez, ~30 min)

> **Antes de empezar, asegurate de tener:** una cuenta con **plan de Claude** · acceso a la cuenta de
> **Canva de 30x** · una cuenta de **Instagram** · y **Git** y **Python** instalados (gratis:
> [git-scm.com](https://git-scm.com) · [python.org](https://python.org)).
> Sin Git no podés clonar el repo; sin Python el worker falla a mitad.

### 1. Instalar Claude Code
Necesitás Claude Code y una cuenta/plan de Claude. Descarga e instrucciones: **https://claude.com/code**
> Si te trabás acá, pedí ayuda a Mateo/IT — es el paso más técnico.

### 2. Conectar Canva (cuenta de 30x)
En Claude, conectá el **conector de Canva** e iniciá sesión con la **cuenta de Canva de 30x**
(la misma donde están las plantillas). Sin esto, la IA no puede crear ni editar diseños.
> ⚠️ Este login **caduca cada ~90 días**. Si un día falla, volvé a conectarlo (ver Problemas comunes).

### 3. Instalar el navegador (Playwright) y loguearte en Instagram
La IA necesita un navegador propio para bajar las slides del referente.
- Instalá el **MCP de Playwright** en Claude *(comando típico: `claude mcp add playwright npx @playwright/mcp@latest` — confirmá con Mateo/IT)*.
- **Abrí ese navegador una vez e iniciá sesión en Instagram.** La sesión queda guardada.
> ⚠️ Si no estás logueada en IG, las descargas fallan (Instagram bloquea a los no logueados).

### 4. Clonar el repo del pipeline
Ahí viven las plantillas, la lógica y los scripts. Abrí una terminal, ubicate donde quieras guardarlo y corré:

```
git clone https://github.com/fckyeslol/30x-carousel-pipeline.git
```
> Más adelante, para traer actualizaciones: `git pull` dentro de esa carpeta.

### 5. Acceso a la cola — ⏸️ PENDIENTE
> **No hagas nada todavía en este paso.** Estamos sacando un cambio para que entres con **tu propio
> usuario de Prewave** (el mismo del board) en vez de manejar una clave. **Te avisamos cuando esté** y
> actualizamos esta guía. Mientras tanto, completá los pasos 1 a 4 — son los que más tardan y no cambian.

---

## PARTE 2 · Prender tu worker (cada vez que vas a trabajar)

> ⏸️ **Esta parte todavía no se puede usar** — depende del **paso 5**, que está pendiente.
> Te avisamos apenas esté listo. Dejamos las instrucciones acá para que ya las tengas.

1. Abrí **Claude Code** dentro de la carpeta `30x-carousel-pipeline`.
2. Pegá esto y dale enter:

```
/loop 20m Worker de carruseles 30x: obtené la PIPELINE_API_KEY del entorno y consultá
GET https://api.prewave.oracle30x.co/api/v1/agent-jobs?status=pending con header X-API-Key.
Si no hay pendientes, no hagas nada. Por cada job pendiente: PATCH status=processing;
reconstruí el carrusel siguiendo AGENT.md (bajá las slides del reference_url con Playwright,
leélas con visión, clasificá, duplicá el template del avatar, rellená en español SIN inventar
datos ni cifras, commit); cerrá con PATCH {status:"done", resultUrl:"<link de Canva>"} o
{status:"failed", error:"<motivo>"} si falla.
```

3. Listo: tu worker revisa la cola **cada 20 minutos** y genera lo que haya.
   - **Mientras esa ventana esté abierta**, el worker vive. Si la cerrás, se apaga.
   - Si preferís no dejarlo prendido, podés pegar el mismo texto **sin** el `/loop 20m` para que procese la cola una sola vez, cuando vos quieras.

---

## PARTE 3 · El flujo de trabajo

1. En **`/diseno`**, una solicitud con referente de IG muestra el botón **"Generar 30x"**.
2. Alguien lo aprieta → el trabajo se **encola**.
3. Tu worker lo toma (en el próximo ciclo) → la tarjeta pasa a **"generando"**.
4. Cuando termina, en la tarjeta aparece **"Ver 30x"** con el link del borrador en Canva.
5. **Vos abrís el Canva, ajustás lo que haga falta, y aprobás.** La IA hace el borrador; vos decidís.

**Qué hace la IA (y qué no):** transpone el contenido del referente al formato 30x, en español, **sin inventar
datos ni cifras**. No decide por vos: siempre queda un borrador para tu revisión.

---

## Problemas comunes

| Síntoma | Qué pasa / qué hacer |
|---|---|
| Aprieto "Generar 30x" y no pasa nada | **No hay ningún worker prendido.** Prendé el tuyo (Parte 2) |
| Canva da error / pide login | El conector caducó (pasa cada ~90 días). Reconectá Canva con la cuenta 30x |
| No baja el referente de Instagram | Tu navegador de Playwright no está logueado en IG. Abrilo e iniciá sesión |
| El job quedó en **"failed"** | Mirá el motivo en el error. Suele ser: referencia que no es carrusel, o alguno de los dos puntos de arriba |
| El diseño salió con la marca equivocada | Todavía no están cargadas las plantillas por avatar (ver Límites) |

---

## Límites actuales (para que no te sorprendan)

- **El worker toma TODOS los pendientes, no solo los tuyos.** El filtro por diseñadora está pendiente de
  desarrollo. Por ahora: **coordinen quién corre el worker** para no pisarse.
- **Las plantillas por avatar aún no están cargadas** → los borradores usan un molde interino, así que la
  *piel* puede no ser la de la cuenta destino. El contenido sí es correcto.
- **No es 100% automático:** requiere tu worker prendido, y re-conectar Canva cada ~90 días.
- **Referentes muy elaborados** (gráficos, timelines, ilustraciones) no se reproducen tal cual: la IA transpone
  el **contenido**, no los gráficos personalizados.

---

## Ayuda

Cualquier duda o si algo falla: **Mateo**. Si el problema es de la solicitud/board, es Prewave; si es del
borrador en Canva, es el molde/plantilla.
