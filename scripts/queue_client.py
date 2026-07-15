#!/usr/bin/env python3
"""Cliente de la cola de Prewave (tabla agent_jobs, PR #306).

El worker usa esto para: listar jobs pendientes, reclamarlos (processing), y cerrarlos
(done + result_url, o failed + error). Auth = pipeline API key (header X-API-Key).

Contrato de endpoints (PR #306, /api/v1):
  GET   /agent-jobs?status=pending          -> [{id, design_request_id, reference_url, avatar_hint, status, ...}]
  PATCH /agent-jobs/:id  {status, result_url?, error?}

Env:
  PREWAVE_API_BASE   (default https://api.prewave.oracle30x.co/api/v1)
  PIPELINE_API_KEY   (obligatorio; el mismo valor seteado en el API en post-deploy)

Uso:
  python queue_client.py list
  python queue_client.py claim <job_id>
  python queue_client.py done  <job_id> <canva_url>
  python queue_client.py fail  <job_id> "<error>"

Como librería:
  from queue_client import list_pending, claim, complete, fail
"""
import json
import os
import sys
import urllib.request

API_BASE = os.environ.get("PREWAVE_API_BASE", "https://api.prewave.oracle30x.co/api/v1").rstrip("/")
API_KEY = os.environ.get("PIPELINE_API_KEY", "")


def _req(method: str, path: str, body: dict | None = None) -> dict | list:
    if not API_KEY:
        raise SystemExit("ERROR: falta PIPELINE_API_KEY en el entorno.")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API_BASE}{path}", data=data, method=method,
        headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else {}


def list_pending() -> list:
    res = _req("GET", "/agent-jobs?status=pending")
    return res.get("items", res) if isinstance(res, dict) else res


def claim(job_id: str) -> dict:
    return _req("PATCH", f"/agent-jobs/{job_id}", {"status": "processing"})


def complete(job_id: str, result_url: str) -> dict:
    # el endpoint espera camelCase resultUrl (verificado en vivo 2026-07-09; snake_case se ignora)
    return _req("PATCH", f"/agent-jobs/{job_id}", {"status": "done", "resultUrl": result_url})


def fail(job_id: str, error: str) -> dict:
    return _req("PATCH", f"/agent-jobs/{job_id}", {"status": "failed", "error": error[:1000]})


def _main(argv) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    try:
        if cmd == "list":
            jobs = list_pending()
            print(json.dumps(jobs, ensure_ascii=False, indent=2))
        elif cmd == "claim":
            print(json.dumps(claim(argv[1]), ensure_ascii=False))
        elif cmd == "done":
            print(json.dumps(complete(argv[1], argv[2]), ensure_ascii=False))
        elif cmd == "fail":
            print(json.dumps(fail(argv[1], argv[2]), ensure_ascii=False))
        else:
            print(f"comando desconocido: {cmd}\n{__doc__}")
            return 2
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
