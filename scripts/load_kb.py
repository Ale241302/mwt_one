#!/usr/bin/env python3
"""
load_kb.py — Sube todos los .md de knowledge/MWT_KB_2026-03-13
al contenedor mwt-knowledge (volumen /kb) y dispara POST /index/.

Uso:
    python scripts/load_kb.py

Requiere:
    - Docker corriendo con mwt-knowledge healthy
    - Variable de entorno KNOWLEDGE_INTERNAL_TOKEN en .env
      (o exportada antes de ejecutar el script)
"""
import os
import subprocess
import sys
from pathlib import Path

# ── Configuración ────────────────────────────────────────────────────────────
KB_LOCAL_DIR  = Path(__file__).parent.parent / "knowledge" / "MWT_KB_2026-03-13"
CONTAINER     = "mwt-knowledge"
KB_REMOTE_DIR = "/kb"
KNOWLEDGE_URL = "http://localhost:8001"
TOKEN         = os.environ.get("KNOWLEDGE_INTERNAL_TOKEN", "")


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=False, text=True)


def main():
    # 1. Verificar que el directorio local existe
    if not KB_LOCAL_DIR.exists():
        print(f"[ERROR] No se encontró el directorio: {KB_LOCAL_DIR}")
        print("        Asegúrate de ejecutar el script desde la raíz del proyecto.")
        sys.exit(1)

    md_files = sorted(KB_LOCAL_DIR.glob("*.md"))
    if not md_files:
        print(f"[ERROR] No hay archivos .md en {KB_LOCAL_DIR}")
        sys.exit(1)

    print(f"[1/3] Encontrados {len(md_files)} archivos .md en {KB_LOCAL_DIR}")

    # 2. Crear directorio /kb dentro del contenedor y copiar los .md
    print(f"\n[2/3] Copiando archivos al contenedor {CONTAINER}:{KB_REMOTE_DIR} ...")
    run(["docker", "exec", CONTAINER, "mkdir", "-p", KB_REMOTE_DIR])

    for md in md_files:
        run(["docker", "cp", str(md), f"{CONTAINER}:{KB_REMOTE_DIR}/{md.name}"])
        print(f"     ✓ {md.name}")

    print(f"\n     {len(md_files)} archivos copiados.")

    # 3. Disparar el endpoint /index/ (requiere JWT con role=CEO)
    print(f"\n[3/3] Disparando POST {KNOWLEDGE_URL}/api/knowledge/index/ ...")
    if not TOKEN:
        print("[WARN] KNOWLEDGE_INTERNAL_TOKEN no está definido.")
        print("       Exporta el token antes de ejecutar:")
        print("       $env:KNOWLEDGE_INTERNAL_TOKEN = 'tu_token_ceo'  # PowerShell")
        print("       export KNOWLEDGE_INTERNAL_TOKEN=tu_token_ceo    # bash")
        print("\n       O ejecuta el endpoint manualmente desde Swagger: http://localhost:8001/docs")
        sys.exit(0)

    try:
        import urllib.request, json
        req = urllib.request.Request(
            f"{KNOWLEDGE_URL}/api/knowledge/index/",
            method="POST",
            headers={
                "Authorization": f"Bearer {TOKEN}",
                "Content-Type": "application/json",
            },
            data=b"{}",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read())
            print("\n[OK] Resultado del indexer:")
            print(f"     files_indexed   : {body.get('files_indexed')}")
            print(f"     chunks_inserted : {body.get('chunks_inserted')}")
            print(f"     chunks_skipped  : {body.get('chunks_skipped')}")
            if body.get("errors"):
                print(f"     errors          : {body['errors']}")
    except Exception as e:
        print(f"[ERROR] llamando /index/: {e}")
        print("        Puedes dispararlo manualmente en: http://localhost:8001/docs")
        sys.exit(1)


if __name__ == "__main__":
    main()
