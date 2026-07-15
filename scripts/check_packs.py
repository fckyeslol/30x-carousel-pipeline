#!/usr/bin/env python3
"""Valida los ADN packs y reporta cuáles están listos para procesar.

Uso: python check_packs.py

Un pack está READY para el orquestador si status=='ready' Y su lienzo de ADN tiene design_id.
El lienzo NO es una plantilla de layout: es materia prima tipográfica (ver AGENT.md → Paso 4).
Reporta por avatar: status, lienzo, y qué falta.
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


def canvas_of(pack):
    """design_id del lienzo de ADN, o None si todavia no se creo."""
    return (pack.get("canvas") or {}).get("design_id") or None


def pending_of(pack):
    return (pack.get("canvas") or {}).get("_pendiente") or ""


def main() -> int:
    if not AVATARS.is_dir():
        print(f"ERROR: no existe {AVATARS}", file=sys.stderr)
        return 1

    packs = sorted(p for p in AVATARS.glob("*/adn.json") if p.parent.name != "_TEMPLATE")
    if not packs:
        print("No hay ADN packs todavía. Crea uno con scripts/new_avatar.py")
        return 0

    ready, draft = [], []
    print(f"{'AVATAR':<22} {'STATUS':<8} {'LIENZO DE ADN'}")
    print("-" * 78)
    for p in packs:
        pack, err = load(p)
        if err:
            print(f"{p.parent.name:<22} ERROR    {err[:40]}")
            continue
        slug = pack.get("avatar", {}).get("slug", p.parent.name)
        status = pack.get("status", "?")
        canvas = canvas_of(pack)
        is_ready = status == "ready" and bool(canvas)
        (ready if is_ready else draft).append(slug)
        flag = "OK" if is_ready else "  "
        print(f"{flag} {slug:<20} {status:<8} {canvas or '(sin lienzo)'}")
        if is_ready and pending_of(pack):
            print(f"{'':<32} ^ pendiente: {pending_of(pack)[:50]}")

    print("-" * 78)
    print(f"READY para procesar: {len(ready)}  -> {', '.join(ready) or '-'}")
    print(f"DRAFT (sin lienzo o sin status): {len(draft)}  -> {', '.join(draft) or '-'}")
    print("\nEl orquestador solo procesa los READY.")
    print("Para activar uno: python scripts/build_canvas.py <slug> (ver AGENT.md).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
