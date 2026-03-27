import os
import urllib.request
import urllib.error
import json
import time

if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                try:
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
                except ValueError:
                    continue

TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

TASKS = [
    {"phase": "FASE 0 — Motor Dimensional + Fixes", "item": "S18-01", "name": "Crear app sizing/ con 6 modelos + seed", "desc": "Implementación de 6 modelos (SizeSystem, Dimension, Entry, Value, Equivalence, Assignment) y seed RW/Marluvas."},
    {"phase": "FASE 0 — Motor Dimensional + Fixes", "item": "S18-02", "name": "FK brand_sku nullable en ExpedienteProductLine", "desc": "Adición de brand_sku (FK) y size_display (property) a ExpedienteProductLine para soporte de tallas."},
    {"phase": "FASE 0 — Motor Dimensional + Fixes", "item": "S18-03", "name": "Fix bug valid_to=null en resolve_client_price()", "desc": "Corrección del filtrado de PriceList para incluir listas con vigencia indefinida (valid_to=null)."},
    {"phase": "FASE 0 — Motor Dimensional + Fixes", "item": "S18-04", "name": "6 campos nullable (diversos modelos)", "desc": "Adición de pricelist_used, base_price, moq_per_size, credit_status, credit_released e incoterms."},
    {"phase": "FASE 0 — Motor Dimensional + Fixes", "item": "S18-05", "name": "Hook post_command_hooks en dispatcher", "desc": "Implementación de lista de hooks post-comando en el dispatcher central."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-06", "name": "Serializers (S18-06)", "desc": "Actualización de serializers para ProductLine, FactoryOrder, Pago, Bundle (detalle) y SizeSystem."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-07", "name": "5 PATCH por estado (S18-07)", "desc": "Implementación de endpoints PATCH validados por estado para CONFIRMADO, PREPARACION, PRODUCCION, DESPACHO y TRANSITO."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-08", "name": "CRUD FactoryOrder (S18-08)", "desc": "GET/POST/PATCH/DELETE de órdenes de fábrica con sincronización automática de factory_order_number."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-09", "name": "POST pagos + confirmación (S18-09)", "desc": "Flujo de creación de pago (PENDING) y confirmación por CEO (CONFIRMED) con recálculo de crédito."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-10", "name": "POST merge (S18-10)", "desc": "Endpoint para fusionar expedientes pre-producción con bloqueo select_for_update."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-11", "name": "POST separate-products / split (S18-11)", "desc": "Endpoint para dividir expedientes moviendo líneas de producto a uno nuevo."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-13", "name": "Actualizar C1 con campos nuevos (S18-13)", "desc": "Extensión del comando C1 para aceptar brand_sku, incoterms y PO number de forma backward compatible."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-15", "name": "recalculate_expediente_credit() (S18-15)", "desc": "Implementación de la única fuente de verdad para credit_exposure y credit_released."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-16", "name": "Sync CreditExposure + EventLog (S18-16)", "desc": "Sincronización del límite de crédito del cliente y registro de logs cuando cambia el flag credit_released."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-17", "name": "Chain resolver pricing (S18-17)", "desc": "Refactorización de resolve_client_price() usando el patrón Chain of Responsibility."},
    {"phase": "FASE 1 — Endpoints Backend", "item": "S18-18", "name": "EventLog estandarizado (S18-18)", "desc": "Campos event_type, previous_status y new_status en EventLog para trazabilidad completa."}
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
            "Estado": {"select": {"name": "No empezado"}},
            "Sprint": {"select": {"name": "Sprint 18"}},
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

if not TOKEN or not DATABASE_ID:
    print("Error: NOTION_TOKEN or NOTION_DATABASE_ID not found in environment.")
    exit(1)

print("Starting task creation in Notion for Sprint 18...")
for task in TASKS:
    create_task(task)
    time.sleep(0.5)
print("Finished.")
