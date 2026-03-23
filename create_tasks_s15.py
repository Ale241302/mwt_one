import os
import urllib.request
import urllib.error
import json
import time

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

TASKS = [
    {"phase": "Fase 0", "item": "S15-01", "name": "Endpoints Write Mockeados", "desc": "Endpoints de marcas, clientes y portal para simular escrituras exitosas (200/201)."},
    {"phase": "Fase 1", "item": "S15-02", "name": "Detalle Expediente CEO / UI", "desc": "Integración de CreditBar, toggle de clientes y glassmorphism en vista detalle."},
    {"phase": "Fase 2", "item": "S15-03", "name": "Brand Console (Tabs 5 & 6)", "desc": "Tab de Pricing (drag and drop) y Tab de Operations (matriz de responsabilidades)."},
    {"phase": "Fase 3", "item": "S15-04", "name": "CEO Credito & Aging Page", "desc": "Página de auditoría comercial con acciones de bloqueo y ajuste de límite."},
    {"phase": "Fase 4", "item": "S15-05", "name": "B2B Portal Glassmorphism / Onboarding", "desc": "Login moderno y Wizard de bienvenida interactivo de 3 pasos."},
    {"phase": "Fase 5", "item": "S15-06", "name": "Dashboard Upgrade (Urgent Actions)", "desc": "Sección Urgent Actions con mapeo de 7 campos y vista Kanban integrada."},
    {"phase": "QA/Estabilidad", "item": "S15-07", "name": "Resolución de Errores de Build / Docker", "desc": "Hotfix para OneDrive en Windows, depuración de SideBar y dependencia sharp."}
]

def create_task(task):
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # Prefixing description with Phase
    desc_content = f"[{task['phase']}] {task['desc']}"
    
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": {
            "Tarea": {"title": [{"text": {"content": task["name"]}}]},
            "Item": {"rich_text": [{"text": {"content": task["item"]}}]},
            "Estado": {"select": {"name": "Done"}},
            "Sprint": {"select": {"name": "Sprint 15"}},
            "Descripción": {"rich_text": [{"text": {"content": desc_content}}]}
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

print("Starting task creation in Notion for Sprint 15...")
for task in TASKS:
    create_task(task)
    time.sleep(0.5)
print("Finished.")
