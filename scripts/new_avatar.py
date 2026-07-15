#!/usr/bin/env python3
"""Crea un ADN pack para un avatar nuevo desde el blueprint _TEMPLATE.

Uso:
    python new_avatar.py "Cora Bilbao" [--handle @cora] [--tagline "..."] [--voice tuteo]

Genera avatars/<slug>/adn.json con nombre+slug (y marca si se pasa). NO sobreescribe si existe.
Luego solo falta pegar los design_id de sus plantillas y poner status:"ready".
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AVATARS = ROOT / "avatars"
TEMPLATE = AVATARS / "_TEMPLATE" / "adn.json"


def slugify(name: str) -> str:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    n = re.sub(r"[^a-zA-Z0-9]+", "-", n).strip("-").lower()
    return n or "avatar"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--slug", default=None)
    ap.add_argument("--handle", default=None)
    ap.add_argument("--tagline", default=None)
    ap.add_argument("--cta", default=None)
    ap.add_argument("--voice", default=None)
    a = ap.parse_args()

    if not TEMPLATE.is_file():
        print(f"ERROR: no existe el blueprint {TEMPLATE}", file=sys.stderr)
        return 1

    slug = a.slug or slugify(a.name)
    dest_dir = AVATARS / slug
    dest = dest_dir / "adn.json"
    if dest.exists():
        print(f"YA EXISTE: {dest} (no se sobreescribe)")
        return 0

    pack = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    pack.pop("_README", None)
    pack["avatar"]["slug"] = slug
    pack["avatar"]["name"] = a.name
    pack["avatar"]["prewave_program_match"] = [a.name]
    if a.handle:  pack["brand"]["handle"] = a.handle
    if a.tagline: pack["brand"]["tagline"] = a.tagline
    if a.cta:     pack["brand"]["cta_default"] = a.cta
    if a.voice:   pack["brand"]["voice"] = a.voice

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"CREADO: {dest}")
    print("Siguiente: pegar los design_id de sus plantillas 30x en 'templates' y poner status:'ready'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
