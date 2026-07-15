#!/usr/bin/env python3
"""Valida los ADN packs y reporta cuáles están listos para procesar.

Uso: python check_packs.py

Un pack está READY para el orquestador si status=='ready' Y tiene al menos un template con design_id.
Reporta por avatar: status, templates con design_id, y qué falta. Sirve de checklist al meter plantillas.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AVATARS = ROOT / "avatars"


def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception as e:
        return None, str(e)


def filled_templates(pack):
    out = []
    for k, v in (pack.get("templates") or {}).items():
        if k.startswith("_"):
            continue
        if isinstance(v, dict) and v.get("design_id"):
            out.append(k)
    return out


def main() -> int:
    if not AVATARS.is_dir():
        print(f"ERROR: no existe {AVATARS}", file=sys.stderr)
        return 1

    packs = sorted(p for p in AVATARS.glob("*/adn.json") if p.parent.name != "_TEMPLATE")
    if not packs:
        print("No hay ADN packs todavía. Crea uno con scripts/new_avatar.py")
        return 0

    ready, draft = [], []
    print(f"{'AVATAR':<22} {'STATUS':<8} {'TEMPLATES CON design_id'}")
    print("-" * 70)
    for p in packs:
        pack, err = load(p)
        if err:
            print(f"{p.parent.name:<22} ERROR    {err[:40]}")
            continue
        slug = pack.get("avatar", {}).get("slug", p.parent.name)
        status = pack.get("status", "?")
        filled = filled_templates(pack)
        is_ready = status == "ready" and len(filled) > 0
        (ready if is_ready else draft).append(slug)
        flag = "OK" if is_ready else "  "
        print(f"{flag} {slug:<20} {status:<8} {', '.join(filled) if filled else '(ninguno)'}")

    print("-" * 70)
    print(f"READY para procesar: {len(ready)}  -> {', '.join(ready) or '-'}")
    print(f"DRAFT (faltan plantillas o status): {len(draft)}  -> {', '.join(draft) or '-'}")
    print("\nEl orquestador solo procesa los READY. Para activar uno: pega design_id + status:'ready'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
