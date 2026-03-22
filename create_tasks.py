import os
import urllib.request
import urllib.error
import json
import time

# Simple .env loader
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

TASKS = [
    {"item": "S12-01", "name": "Dividir services.py (1,371 líneas) en 9 módulos", "desc": "Incluye matriz C1-C22, estructura de directorios y comandos bash. PROMPT_ANTIGRAVITY_SPRINT12.md"},
    {"item": "S12-02", "name": "Consolidar services_sprint5.py (312 líneas)", "desc": "En los módulos de services/ LOTE_SM_SPRINT12.md"},
    {"item": "S12-03", "name": "Colapsar 18+ clases APIView en CommandDispatchView", "desc": "Interno (sin cambiar URLs públicas) PROMPT_ANTIGRAVITY_SPRINT12.md"},
    {"item": "S12-04", "name": "Documentación API con drf-spectacular", "desc": "Swagger UI en /api/docs/ GUIA_ALE_SPRINT12.md"},
    {"item": "S12-05", "name": "Paginación opt-in + error responses", "desc": "Solo 3 vistas allowlist + envelope aditivo GUIA_ALE_SPRINT12.md"},
    {"item": "S12-06", "name": "Limpieza: db_index, scripts, logger.ts", "desc": "4 campos con index, mover scripts sueltos, reemplazar console por logger. LOTE_SM_SPRINT12.md"},
    {"item": "S12-07", "name": "Pipelines ci.yml y deploy.yml", "desc": "Healthcheck + rollback automático, secrets en GitHub. PROMPT_ANTIGRAVITY_SPRINT12.md"},
    {"item": "S12-08", "name": "Hooks useFetch / useCRUD", "desc": "Auto-detect de formato paginado/plano, migrar 3 páginas. LOTE_SM_SPRINT12.md"},
    {"item": "S12-09", "name": "DrawerShell.tsx + hook useFormSubmit", "desc": "Reducir duplicación de modals >=50%. LOTE_SM_SPRINT12.md"},
    {"item": "S12-10", "name": "Carry-over Sprint 11: Portal B2B / Productos", "desc": "Si no se completaron en el sprint anterior. LOTE_SM_SPRINT12.md"},
    {"item": "S12-11", "name": "Módulo Inventario: modelo InventoryEntry", "desc": "4 endpoints, vista por nodo/producto. PROMPT_ANTIGRAVITY_SPRINT12.md"},
    {"item": "S12-12", "name": "WhatsApp Business API: webhook, log, Celery", "desc": "Consola CEO (condicional a Meta). PROMPT_ANTIGRAVITY_SPRINT12.md"},
    {"item": "S12-13", "name": "Checklist de tests: QA integral", "desc": "Refactorización, frontend, CI/CD, inventario, WhatsApp y regresión. GUIA_ALE_SPRINT12.md"}
]

def create_task(task):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Tarea": {"title": [{"text": {"content": task["name"]}}]},
            "Item": {"rich_text": [{"text": {"content": task["item"]}}]},
            "Estado": {"select": {"name": "Done"}},
            "Sprint": {"select": {"name": "Sprint 12"}},
            "Descripción": {"rich_text": [{"text": {"content": task["desc"]}}]}
        }
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as res:
            print(f"Created: {task['item']} - {task['name']}")
    except Exception as e:
        print(f"Error creating {task['item']}: {e}")
        if isinstance(e, urllib.error.HTTPError):
            print(e.read().decode())

for task in TASKS:
    create_task(task)
    time.sleep(0.5) # Avoid rate limits
