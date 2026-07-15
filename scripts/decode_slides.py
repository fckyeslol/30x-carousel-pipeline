#!/usr/bin/env python3
"""Decodifica el JSON base64 que vuelca el navegador (Paso 1 del AGENT.md) a imágenes.

El MCP de Playwright, al hacer fetch de las slides dentro de la sesión y guardarlas con
`filename`, produce un JSON = array de data-URLs (`data:image/...;base64,...`) o strings 'ERR:...'.
Este helper las convierte en archivos slide-01.jpg, slide-02.jpg, ... listos para leer con visión.

Uso:
    python decode_slides.py <ruta-json> [carpeta-salida]

Salida: imprime una línea por slide (OK/ERR) y escribe los archivos en la carpeta de salida
(por defecto ./slides junto al JSON).
"""
import base64
import json
import re
import sys
from pathlib import Path

DATA_URL = re.compile(r"data:(image/(\w+));base64,(.*)", re.S)


def decode(json_path: str, out_dir: str | None = None) -> int:
    src = Path(json_path)
    if not src.is_file():
        print(f"ERROR: no existe {src}", file=sys.stderr)
        return 1

    data = json.loads(src.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print("ERROR: el JSON no es un array de data-URLs", file=sys.stderr)
        return 1

    out = Path(out_dir) if out_dir else src.parent / "slides"
    out.mkdir(parents=True, exist_ok=True)

    ok = 0
    for i, item in enumerate(data, 1):
        if not isinstance(item, str) or item.startswith("ERR"):
            print(f"slide {i:02d}: ERR {str(item)[:80]}")
            continue
        m = DATA_URL.match(item)
        if not m:
            print(f"slide {i:02d}: sin match data-url")
            continue
        ext = m.group(2)
        raw = base64.b64decode(m.group(3))
        fn = out / f"slide-{i:02d}.{ext}"
        fn.write_bytes(raw)
        print(f"slide {i:02d}: OK -> {fn} ({len(raw)} bytes)")
        ok += 1

    print(f"\n{ok}/{len(data)} slides decodificadas en {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(decode(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
