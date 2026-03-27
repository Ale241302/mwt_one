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
    {"phase": "FASE 0 — BUGS CRÍTICOS", "item": "S17-01", "name": "Fix command_preparacion_despacho (PREPARACION → DESPACHO)", "desc": "Corrección de la transición en constants.py para que el estado DESPACHO sea alcanzable."},
    {"phase": "FASE 0 — BUGS CRÍTICOS", "item": "S17-02", "name": "Asegurar command_despacho_transito (DESPACHO → TRANSITO)", "desc": "Creación del comando C11B y actualización de la UI (ExpedienteAccordion y GateMessage)."},
    {"phase": "FASE 0 — BUGS CRÍTICOS", "item": "S17-03", "name": "Verificar REOPEN en dispatcher", "desc": "Validación de que REOPEN esté correctamente conectado en COMMAND_SPEC, HANDLERS y URLs."},
    {"phase": "FASE 0 — BUGS CRÍTICOS", "item": "S17-04", "name": "Auditar, endurecer y completar endpoints Portal", "desc": "Implementación de 3 endpoints con aislamiento de tenant (404 uniforme) y exclusión de campos CEO-ONLY."},
    {"phase": "FASE 0 — BUGS CRÍTICOS", "item": "S17-05", "name": "Fix firma handle_c1", "desc": "Unificación de la firma de handle_c1(payload, user) para consistencia con el dispatcher."},
    {"phase": "FASE 0 — BUGS CRÍTICOS", "item": "S17-06", "name": "Eliminar páginas frontend duplicadas", "desc": "Limpieza del directorio frontend/src/app/[lang]/dashboard/expedientes/ para dejar solo la versión canónica."},
    {"phase": "FASE 0 — BUGS CRÍTICOS", "item": "S17-07", "name": "Integrar C22 al dispatcher central", "desc": "Migración de la lógica de C22 a apps/expedientes/services/ y eliminación del módulo aislado."},
    {"phase": "FASE 1 — MODELO DE DATOS EXTENDIDO", "item": "S17-08", "name": "~30 campos operativos en modelo Expediente", "desc": "Adición de campos operativos organizados por estado con help_text descriptivos."},
    {"phase": "FASE 1 — MODELO DE DATOS EXTENDIDO", "item": "S17-09", "name": "Modelo ExpedienteProductLine", "desc": "Creación del modelo relacional con FK a ProductMaster y soporte para múltiples orígenes de precio."},
    {"phase": "FASE 1 — MODELO DE DATOS EXTENDIDO", "item": "S17-10", "name": "Modelo FactoryOrder", "desc": "Modelo relacional para órdenes de fábrica con sincronización automática del factory_order_number."},
    {"phase": "FASE 1 — MODELO DE DATOS EXTENDIDO", "item": "S17-11", "name": "Modelo ExpedientePago", "desc": "Registro operativo de pagos que coexiste con el ledger PaymentLine."},
    {"phase": "FASE 1 — MODELO DE DATOS EXTENDIDO", "item": "S17-12", "name": "payment_grace_days en ClientSubsidiary", "desc": "Configuración de días de gracia para cobranza en el modelo de clientes."},
    {"phase": "FASE 1 — MODELO DE DATOS EXTENDIDO", "item": "S17-13", "name": "Admin + Migración consolidada", "desc": "Registro de inlines en el admin y generación de una única migración aditiva."},
    {"phase": "FASE 1 — MODELO DE DATOS EXTENDIDO", "item": "S17-14", "name": "Tests: transiciones, portal, modelos nuevos", "desc": "Cobertura completa de tests para transiciones, seguridad de portal e integridad de modelos."}
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
            "Sprint": {"select": {"name": "Sprint 17"}},
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

print("Starting task creation in Notion for Sprint 17...")
for task in TASKS:
    create_task(task)
    time.sleep(0.5)
print("Finished.")
