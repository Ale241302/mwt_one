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
    {"item": "S13-01", "name": "Corregir DAI 0%→14% partida 6403.99.90", "desc": "0 — KB ENT_COMERCIAL_COSTOS. Corregir arancel."},
    {"item": "S13-02", "name": "Agregar cost_category a CostLine", "desc": "1 — Modelo models.py, financial.py, enums.py, serializers.py"},
    {"item": "S13-03", "name": "Agregar cost_behavior nullable", "desc": "1 — Modelo models.py, financial.py, enums.py"},
    {"item": "S13-04", "name": "Multi-moneda (exchange_rate, base_currency)", "desc": "1 — Modelo models.py, financial.py, serializers.py. amount_base_currency."},
    {"item": "S13-05", "name": "pre_check_viability en C4", "desc": "2 — Lógica services/commands_registro.py, settings/. Fallback degradado."},
    {"item": "S13-06", "name": "ART-13 (Certificado Origen) + ART-14 (DU-E)", "desc": "2 — Lógica enums.py, models.py, admin.py, ARTIFACT_REGISTRY"},
    {"item": "S13-07", "name": "Aforo aduanero (verde/amarillo/rojo)", "desc": "3 — Datos models.py, admin.py, ENT_OPS_EXPEDIENTE"},
    {"item": "S13-08", "name": "Checklist de tests: Sprint 13", "desc": "Final tests/test_sprint13.py (CREAR). +30 tests: CostLine v2, viabilidad, artefactos, regresión"}
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
            "Sprint": {"select": {"name": "Sprint 13"}},
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
    time.sleep(0.5)

print("Sprint 13 upload COMPLETE")
