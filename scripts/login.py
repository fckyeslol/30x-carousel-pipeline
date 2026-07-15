"""Login a Prewave para el worker de carruseles.

Pide tu email y tu contrasena de Prewave y guarda tu token en .prewave-token
(ignorado por git). El worker lo lee de ahi: no hay que pegarlo en ningun lado.

    python scripts/login.py

IMPORTANTE — corre ESTO EN TU TERMINAL, no se lo pidas a Claude Code:
la contrasena se escribe a ciegas (no se ve, no queda en el historial de la
terminal ni en la transcripcion del chat). Si Claude lo corriera por vos, no
podria escribirla igual: su terminal no es interactiva.

El token dura 30 dias. Cuando la cola empiece a dar 401, volve a correr esto.
"""
import getpass
import json
import pathlib
import sys
import urllib.error
import urllib.request

API_BASE = "https://api.prewave.oracle30x.co/api/v1"
TOKEN_FILE = pathlib.Path(__file__).resolve().parent.parent / ".prewave-token"


def main() -> int:
    print("Login de Prewave (el mismo usuario del board de Diseno)\n")
    email = input("  Email: ").strip()
    if not email:
        print("\nERROR: hace falta el email.")
        return 1

    # getpass NO muestra lo que escribis. Es a proposito: escribi a ciegas y enter.
    password = getpass.getpass("  Contrasena (no se ve mientras escribis): ")
    if not password:
        print("\nERROR: hace falta la contrasena.")
        return 1

    req = urllib.request.Request(
        f"{API_BASE}/auth/login",
        data=json.dumps({"email": email, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        res = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = json.loads(e.read()).get("error", "")
        except Exception:
            pass
        if "Google sign-in" in detail:
            print("\nERROR: tu cuenta entra con Google, no tiene contrasena.")
            print("Avisale a Mateo: hay que darte una para poder sacar el token.")
        elif e.code == 401:
            print("\nERROR: email o contrasena incorrectos.")
        else:
            print(f"\nERROR: el login fallo (HTTP {e.code}). {detail}")
        return 1
    except Exception as e:
        print(f"\nERROR: no se pudo contactar a Prewave: {e}")
        return 1

    token = res.get("token")
    if not token:
        print("\nERROR: Prewave no devolvio un token.")
        return 1

    TOKEN_FILE.write_text(token, encoding="utf-8")
    try:
        TOKEN_FILE.chmod(0o600)  # solo tu usuario puede leerlo (no-op en Windows)
    except Exception:
        pass

    user = res.get("user") or {}
    perms = res.get("permissions") or []
    puede = [p for p in perms if p.startswith("design:")]
    print(f"\nOK. Hola {user.get('name') or user.get('email') or email}.")
    print(f"Token guardado en {TOKEN_FILE.name} (dura 30 dias, no lo subas a ningun lado).")
    if puede:
        print(f"Permisos de diseno: {', '.join(puede)}")
    else:
        print("AVISO: tu usuario no tiene permisos de diseno; la cola te va a dar 403.")
    print("\nYa podes abrir Claude Code y pedirle que prenda tu worker.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
