# Cómo pedir las plantillas de Canva por avatar

Objetivo: que lleguen listas para pegar en `avatars/<slug>/adn.json` sin retrabajo.

## Opción recomendada (menos trabajo para el diseñador): 1 master por avatar

Un solo diseño de Canva por avatar — **"Master 30x — <Avatar>"** — que contenga sus láminas
branded, una de cada tipo que vayan a usar, en este orden sugerido:

1. Portada (cover)
2. Dato / estadística  ← si hacen muchos de datos, incluir **2–3 páginas** de este tipo
3. Comparativo ✕/✓     ← idem, **varias páginas** si es un formato frecuente
4. Tip de un bloque     ← idem
5. Principio / quote
6. Proceso 01·02·03
7. Insight / transición
8. Cierre / CTA

> **Por qué varias páginas de un tipo:** la API de Canva no duplica páginas. Para carruseles largos,
> el master debe traer suficientes "slots" de los tipos repetibles (dato, comparativo, tip) para recortar.

Me mandan **el link** y yo mapeo qué página = qué layout, extraigo el `design_id` y lleno el `adn.json`.

## Opción alterna: 1 diseño por tipo

Si ya los tienen separados, una tabla por avatar:

| Layout | Link de Canva |
|---|---|
| cover | … |
| data | … |
| comparative | … |
| … | … |

## Qué link mandar (para sacar el `design_id` sin fricción)

- **Mejor:** el link de la barra de direcciones con el diseño abierto — contiene el `design_id`:
  `https://www.canva.com/design/`**`DAxxxxxxxxx`**`/.../edit`  → el `DAxxxxxxxxx` es el design_id.
- También sirve el link corto de compartir (`canva.com/d/xxxx` o `canva.link/xxxx`); yo lo resuelvo.
- **Permisos:** que el diseño esté en la **cuenta de Canva de 30x** (la que está conectada al MCP),
  o compartido con ella. Si está en otra cuenta, el agente no lo ve.

## Datos de marca por avatar (junto con los links)

Para cada avatar, además de los links: **handle** oficial, **tagline** fija, **CTA** de cierre, y **voz**
(tú/vos). Eso va en `brand` del `adn.json`. Con links + estos 4 datos, el pack queda `ready`.
