"""Genera el HTML del LIENZO DE ADN de un avatar.

El lienzo NO es una plantilla de layout. Es materia prima tipografica: un diseno con la
fuente y el fondo del avatar ya horneados, mas una reserva de bloques de texto vacios.
Existe solo porque la API de Canva no puede crear texto ni cambiar la familia tipografica
(ver AGENT.md -> Paso 4). La estructura de cada carrusel SIEMPRE viene del referente.

Uso:
    python scripts/build_canvas.py cinthya
    python scripts/build_canvas.py guillermo --pages 12 --blocks 8

Despues:
    1. git add build/ && git commit && git push        (necesita URL publica para el import)
    2. import-design-from-url con la URL cruda de GitHub
    3. resize-design a 1080x1350
    4. pegar el design_id en avatars/<slug>/adn.json -> canvas.design_id  + status ready
"""
import argparse
import base64
import json
import pathlib
import re
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch_font_faces(family: str) -> str:
    """Baja la familia de Google Fonts y la devuelve como @font-face con la fuente embebida.

    Se embebe en base64 a proposito: el import de Canva no garantiza resolver un <link>
    externo, y una fuente que no carga degrada en silencio a un serif generico.
    """
    slug = family.replace(" ", "+")
    url = f"https://fonts.googleapis.com/css2?family={slug}:ital,wght@0,400;0,700;1,400&display=swap"
    try:
        css = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode()
    except Exception:
        # no todas las familias tienen las 3 variantes; reintentar con la basica
        url = f"https://fonts.googleapis.com/css2?family={slug}&display=swap"
        css = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode()

    faces = []
    for block in re.findall(r"@font-face\s*\{[^}]+\}", css):
        m = re.search(r"url\((https://[^)]+)\)", block)
        if not m:
            continue
        style = "italic" if "font-style: italic" in block else "normal"
        weight = re.search(r"font-weight:\s*(\d+)", block)
        weight = weight.group(1) if weight else "400"
        data = urllib.request.urlopen(urllib.request.Request(m.group(1), headers=UA), timeout=30).read()
        b64 = base64.b64encode(data).decode()
        faces.append(
            f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
        )
        print(f"  {family} {style} {weight}: {len(data):,} bytes")
    if not faces:
        sys.exit(f"ERROR: no se pudo bajar ninguna variante de '{family}'")
    return "\n".join(faces)


def build(slug: str, pages: int, blocks: int) -> pathlib.Path:
    adn_path = ROOT / "avatars" / slug / "adn.json"
    if not adn_path.exists():
        sys.exit(f"ERROR: no existe {adn_path}")
    adn = json.loads(adn_path.read_text(encoding="utf-8"))

    vi = adn.get("visual_identity") or {}
    family = (vi.get("tipografia") or {}).get("familia")
    palette = vi.get("paleta") or []
    if not family:
        sys.exit(f"ERROR: {slug} no tiene visual_identity.tipografia.familia — el ADN esta incompleto")
    if not palette:
        sys.exit(f"ERROR: {slug} no tiene visual_identity.paleta — el ADN esta incompleto")

    bg = palette[0]["hex"]
    fg = palette[1]["hex"] if len(palette) > 1 else "#000000"
    accent = palette[-1]["hex"]
    name = adn["avatar"]["name"]

    print(f"Lienzo de {name}: {family} | fondo {bg} | texto {fg} | acento {accent}")
    faces = fetch_font_faces(family)

    # Los bloques nacen con la familia correcta (unico dato que la API no puede cambiar
    # despues). Cuerpo, color y posicion los define el agente por cada referente.
    parts = [
        "<meta charset='utf-8'>",
        f"<title>Lienzo ADN — {name}</title>",
        "<!-- LIENZO DE ADN. Generado por scripts/build_canvas.py. NO es una plantilla de layout:",
        "     no contiene estructura. Ver AGENT.md -> Paso 4. -->",
        "<style>",
        faces,
        f"""
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  .page {{ width:1080px; height:1350px; background:{bg}; color:{fg};
           font-family:'{family}', sans-serif; padding:88px; }}
  .b {{ font-size:48px; line-height:1.2; margin-bottom:24px; }}
  .b.accent {{ color:{accent}; }}
""",
        "</style>",
    ]
    for p in range(1, pages + 1):
        parts.append(f"<div data-document-role='page' data-label='Lienzo {p}'>")
        for b in range(1, blocks + 1):
            cls = "b accent" if b == 1 else "b"
            parts.append(f"  <div class='{cls}'>Bloque {p}.{b}</div>")
        parts.append("</div>")

    out = ROOT / "build" / f"canvas-{slug}.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"\nOK -> {out.relative_to(ROOT)} ({out.stat().st_size:,} bytes, {pages} paginas x {blocks} bloques)")
    print(f"URL tras pushear:\n  https://raw.githubusercontent.com/fckyeslol/30x-carousel-pipeline/master/build/canvas-{slug}.html")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Genera el HTML del lienzo de ADN de un avatar")
    ap.add_argument("slug", help="slug del avatar (carpeta en avatars/)")
    ap.add_argument("--pages", type=int, default=12, help="paginas del lienzo (la API no duplica paginas)")
    ap.add_argument("--blocks", type=int, default=8, help="bloques de texto de reserva por pagina")
    a = ap.parse_args()
    build(a.slug, a.pages, a.blocks)
