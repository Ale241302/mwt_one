"""
Migration Script: Old PHP API (api_expedientes_mwt_one) → New Django API (mwt_one)

Reads all expedientes from the old system's REST API and creates them
in the new Django system via its command-based API.

Usage:
    python migrate_expedientes.py [--dry-run] [--order MWT-XXXX-YYYY] [--limit N]

Requirements:
    pip install requests
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OLD_API_BASE = "https://muitowork.com/api-tracking"
OLD_API_AUTH = {
    "keyhash": "e474389ae582ee303d6a7d0c6307e6beb373015edfa7b67f1a02bab62367d66f",
    "keyuser": "e474389ae582ee303d6a7d0c6307e6beb373015edfa7b67f1a02bab62367d66f",
}

# New Django API — update these for your deployment
NEW_API_BASE = "http://localhost:8000/api"
NEW_API_TOKEN = ""  # Set via --token or env var MWT_API_TOKEN

# Throttle between old API requests (seconds)
REQUEST_DELAY = 1.0

# State mapping: old status → (new ExpedienteStatus, last command executed)
STATUS_MAP = {
    "Creación":    ("REGISTRO", None),
    "Crédito":     ("REGISTRO", None),
    "Producción":  ("PRODUCCION", "C5"),
    "produccion":  ("PRODUCCION", "C5"),
    "Preparación": ("PREPARACION", "C6"),
    "Despacho":    ("DESPACHO", "C11"),
    "Tránsito":    ("TRANSITO", "C11"),
    "transito":    ("TRANSITO", "C11"),
    "Pago":        ("EN_DESTINO", "C12"),
    "pagado":      ("_PAGADO_DYNAMIC", "C14"),  # resolved dynamically — see determine_target_status
    "Archivada":   ("CERRADO", "C14"),           # archived = closed with metadata flag
    "Cerrado":     ("CERRADO", "C14"),
    "Cancelado":   ("CANCELADO", "CANCEL"),
}

# Old status → action name for fetching detail
STATUS_ACTION_MAP = {
    "Creación":    "getPreforma",
    "Crédito":     "getCreditOrderData",
    "Producción":  "listProduccionInfo",
    "Preparación": "listPreparacionInfo",
    "Despacho":    "listDespachoInfo",
    "Tránsito":    "listTransitoInfo",
    "Pago":        "listPagoInfo",
}

# Actions to fetch regardless of current status (accumulate historical data)
ALL_ACTIONS = [
    "getPreforma",
    "getCreditOrderData",
    "listProduccionInfo",
    "listPreparacionInfo",
    "listDespachoInfo",
    "listTransitoInfo",
    "listPagoInfo",
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("migrate")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class OldExpediente:
    """Aggregated data from the old system for one expediente."""
    order_number: str
    order_status: str
    order_id: int | None = None
    customer_name: str | None = None
    customer_id: int | None = None
    order_full_price: float | None = None
    order_created_date: str | None = None
    number_purchase: str | None = None  # proforma number
    operado_mwt: int | None = None
    order_parent_id: int | None = None
    # Detail data per action
    preforma: dict | None = None
    credit: dict | None = None
    produccion: dict | None = None
    preparacion: dict | None = None
    despacho: dict | None = None
    transito: dict | None = None
    pago: dict | None = None
    # Raw responses for debugging
    raw: dict = field(default_factory=dict)


@dataclass
class MigrationResult:
    order_number: str
    success: bool
    new_expediente_id: str | None = None
    commands_executed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str | None = None


# ---------------------------------------------------------------------------
# Old API Client
# ---------------------------------------------------------------------------

class OldApiClient:
    """Client for the old PHP tracking API."""

    def __init__(self, base_url: str, auth: dict, delay: float = 1.0):
        self.base_url = base_url
        self.auth = auth
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _post(self, endpoint: str, extra_body: dict | None = None) -> dict | list | None:
        url = f"{self.base_url}/{endpoint}"
        body = {**self.auth}
        if extra_body:
            body.update(extra_body)
        try:
            resp = self.session.post(url, json=body, timeout=30)
            if resp.status_code == 503:
                log.warning("503 from %s — server may be blocking. Skipping.", url)
                return None
            resp.raise_for_status()
            time.sleep(self.delay)
            return resp.json()
        except requests.exceptions.JSONDecodeError:
            log.warning("Non-JSON response from %s: %s", url, resp.text[:200])
            return None
        except requests.exceptions.RequestException as e:
            log.error("Request failed for %s: %s", url, e)
            return None

    def list_orders(self) -> list[dict]:
        """Fetch all expedientes from order.php."""
        data = self._post("order.php")
        if data is None:
            return []
        if isinstance(data, dict) and "orders" in data:
            return data["orders"]
        if isinstance(data, list):
            return data
        # Some responses wrap in different keys
        for key in ("data", "result", "expedientes"):
            if isinstance(data, dict) and key in data:
                return data[key]
        log.warning("Unexpected order list format: %s", type(data))
        return data if isinstance(data, list) else []

    def get_detail(self, order_number: str, action: str) -> dict | None:
        """Fetch detail for a specific order and action from api.php."""
        data = self._post("api.php", {
            "order_number": order_number,
            "action": action,
        })
        if isinstance(data, dict):
            return data
        return None

    def fetch_full_expediente(self, order_summary: dict) -> OldExpediente:
        """Fetch all available detail for one expediente."""
        order_number = order_summary.get("order_number", "")
        exp = OldExpediente(
            order_number=order_number,
            order_status=order_summary.get("order_status", ""),
            order_id=order_summary.get("order_id"),
            customer_name=order_summary.get("customer_name"),
            customer_id=order_summary.get("customer"),
            order_full_price=_to_float(order_summary.get("order_full_price")),
            order_created_date=order_summary.get("order_created_date"),
            number_purchase=order_summary.get("number_purchase"),
            operado_mwt=order_summary.get("operado_mwt"),
            order_parent_id=order_summary.get("order_parent_id"),
        )

        # Fetch all actions to accumulate complete data
        action_field_map = {
            "getPreforma": "preforma",
            "getCreditOrderData": "credit",
            "listProduccionInfo": "produccion",
            "listPreparacionInfo": "preparacion",
            "listDespachoInfo": "despacho",
            "listTransitoInfo": "transito",
            "listPagoInfo": "pago",
        }
        for action in ALL_ACTIONS:
            log.debug("  Fetching %s for %s", action, order_number)
            detail = self.get_detail(order_number, action)
            field_name = action_field_map[action]
            if detail and not _is_error_response(detail):
                setattr(exp, field_name, detail)
            exp.raw[action] = detail

        return exp


# ---------------------------------------------------------------------------
# New API Client
# ---------------------------------------------------------------------------

class NewApiClient:
    """Client for the new Django REST API."""

    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        })

    def create_expediente(self, payload: dict) -> dict | None:
        """POST /api/expedientes/create/ — executes C1."""
        url = f"{self.base_url}/expedientes/create/"
        try:
            resp = self.session.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            log.error("Create expediente failed: %s — %s",
                      e, getattr(e.response, "text", "")[:500] if hasattr(e, "response") else "")
            return None

    def execute_command(self, expediente_id: str, cmd_id: str, payload: dict | None = None) -> dict | None:
        """POST /api/expedientes/<pk>/command/<cmd_id>/ — execute a command."""
        url = f"{self.base_url}/expedientes/{expediente_id}/command/{cmd_id}/"
        body = payload or {}
        try:
            resp = self.session.post(url, json=body, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            log.error("Command %s on %s failed: %s — %s",
                      cmd_id, expediente_id, e,
                      getattr(e.response, "text", "")[:500] if hasattr(e, "response") else "")
            return None

    def list_expedientes(self) -> list[dict]:
        """GET /api/ui/expedientes/ — check existing."""
        url = f"{self.base_url}/ui/expedientes/"
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            return data.get("results", data) if isinstance(data, dict) else data
        except requests.exceptions.RequestException:
            return []


# ---------------------------------------------------------------------------
# Data Transformation: Old → New
# ---------------------------------------------------------------------------

def build_c1_payload(exp: OldExpediente, client_map: dict, brand_id: str | None) -> dict:
    """
    Build the payload for C1 (Create Expediente) in the new system.

    The new system's C1 expects:
    {
        "legal_entity_id": "<entity_id>",  -- e.g. "MWT-CR"
        "brand_id": <brand_pk>,
        "client_id": <legal_entity_pk>,
        "destination": "CR" | "USA",
        "mode": "MWT" | "CLIENT",
        ...
    }
    """
    # Determine client in new system
    client_key = exp.customer_name or str(exp.customer_id or "unknown")
    client_id = client_map.get(client_key)

    payload = {
        "legal_entity_id": "MWT-CR",  # Default emitting entity
        "destination": "CR",           # Default; adjust if needed
        "mode": "MWT" if exp.operado_mwt == 1 else "CLIENT",
        "metadata": {
            "migrated_from": "api_expedientes_mwt_one",
            "original_order_number": exp.order_number,
            "original_status": exp.order_status,
            "original_created": exp.order_created_date,
            "original_customer": exp.customer_name,
            "original_price": exp.order_full_price,
        },
    }

    if brand_id:
        payload["brand_id"] = brand_id
    if client_id:
        payload["client_id"] = client_id

    # Flag archived expedientes
    if exp.order_status.lower() == "archivada":
        payload["metadata"]["archived"] = True

    return payload


def build_c2_payload(exp: OldExpediente) -> dict | None:
    """Build C2 (Register Proforma) payload from old preforma data."""
    pf = exp.preforma
    if not pf:
        return None
    return {
        "artifact_type": "ART-02",
        "payload": {
            "number_purchase": pf.get("number_purchase") or exp.number_purchase,
            "preforma_url": pf.get("preformar"),
            "miniatura_url": pf.get("miniatura"),
            "migrated": True,
        },
    }


def build_production_payload(exp: OldExpediente) -> dict | None:
    """Build payload for production-related data (used in C5 transition)."""
    prod = exp.produccion
    if not prod:
        return None
    return {
        "payload": {
            "fecha_inicio": prod.get("fechai"),
            "fecha_fin": prod.get("fechaf"),
            "status": prod.get("status"),
            "sap_records": prod.get("sap", []),
            "migrated": True,
        },
    }


def build_preparacion_payload(exp: OldExpediente) -> dict | None:
    """Build payload for preparacion artifacts (C7-C10)."""
    prep = exp.preparacion
    if not prep:
        return None

    artifacts = []

    # Packing list (ART-07)
    pack_det = prep.get("pack_detallado") or prep.get("packDetallado")
    if pack_det:
        artifacts.append({
            "artifact_type": "ART-07",
            "payload": {
                "pack_url": pack_det.get("pack"),
                "caja_url": pack_det.get("caja"),
                "miniatura_url": pack_det.get("miniatura"),
                "migrated": True,
            },
        })

    # Cotizacion (ART-08)
    cot = prep.get("cotizacion")
    if cot:
        artifacts.append({
            "artifact_type": "ART-08",
            "payload": {
                "cotizacion_url": cot.get("cotizacion"),
                "miniatura_url": cot.get("miniatura"),
                "migrated": True,
            },
        })

    # Products info
    products = prep.get("products", [])

    return {
        "artifacts": artifacts,
        "shipping_info": {
            "method": prep.get("order_shipping_method"),
            "price": _to_float(prep.get("order_shipping_price")),
            "incoterms": prep.get("Incoterms"),
            "code_incoterms": prep.get("Code_incoterms"),
            "address": {
                "street": prep.get("address_street"),
                "city": prep.get("address_city"),
                "postal_code": prep.get("address_post_code"),
                "phone": prep.get("address_telephone"),
            },
        },
        "products": products,
        "migrated": True,
    }


def build_despacho_payload(exp: OldExpediente) -> dict | None:
    """Build payload for despacho artifacts (ART-09 invoice, ART-05 shipping)."""
    desp = exp.despacho
    if not desp:
        return None

    result: dict[str, Any] = {"artifacts": [], "migrated": True}

    # Shipping doc (ART-05)
    shipping = desp.get("shipping")
    if shipping:
        result["artifacts"].append({
            "artifact_type": "ART-05",
            "payload": {
                "number_guia": shipping.get("number_guia"),
                "guia_url": shipping.get("guia"),
                "fechas": shipping.get("fechas"),
                "fecha_arribo": shipping.get("fecha_arribo"),
                "link": shipping.get("link"),
                "puerto_intermedio": shipping.get("puerto_intermedio"),
                "despacho_name": shipping.get("nomber_despacho"),
                "arribo_name": shipping.get("nomber_arribo"),
                "migrated": True,
            },
        })

    # Commercial invoice (ART-09)
    invoice = desp.get("invoice")
    if invoice:
        result["artifacts"].append({
            "artifact_type": "ART-09",
            "payload": {
                "number_invoice": invoice.get("number_invoice"),
                "invoice_url": invoice.get("invoice"),
                "certificado_url": invoice.get("certificado"),
                "number_invoice_mwt": invoice.get("number_invoice_mwt"),
                "invoice_mwt_url": invoice.get("invoice_mwt"),
                "migrated": True,
            },
        })

    # Payment date calculation
    if desp.get("customer_payment_time"):
        result["customer_payment_time"] = desp["customer_payment_time"]

    return result


def build_transito_payload(exp: OldExpediente) -> dict | None:
    """Build payload for tránsito data."""
    trans = exp.transito
    if not trans:
        return None

    result: dict[str, Any] = {"migrated": True}

    if trans.get("fecha_arribo"):
        result["fecha_arribo"] = trans["fecha_arribo"]
    if trans.get("puerto_intermedio"):
        result["puerto_intermedio"] = trans["puerto_intermedio"]

    pack = trans.get("pack")
    if pack:
        result["pack"] = {
            "pack_url": pack.get("pack"),
            "name": pack.get("nomb_pack"),
            "miniatura_url": pack.get("miniatura"),
        }

    return result


def build_payment_payloads(exp: OldExpediente) -> list[dict]:
    """Build C21 (Register Payment) payloads from old pago data."""
    pago = exp.pago
    if not pago:
        return []

    # pago can be a list of payments or a single dict
    payments = pago if isinstance(pago, list) else pago.get("pagos", [pago])

    result = []
    for p in payments:
        if not isinstance(p, dict):
            continue
        amount = _to_float(p.get("cantidad_pago"))
        if amount is None or amount == 0:
            continue
        result.append({
            "amount": amount,
            "currency": "USD",
            "method": p.get("metodo_pago", "transfer"),
            "reference": p.get("comprobante", ""),
            "metadata": {
                "original_id": p.get("id"),
                "tipo_pago": p.get("tipo_pago"),
                "fecha_pago": p.get("fecha_pago"),
                "nombre": p.get("nombre"),
                "migrated": True,
            },
        })

    return result


# ---------------------------------------------------------------------------
# Command sequence to advance expediente to target status
# ---------------------------------------------------------------------------

# Ordered list of (command, target_status, payload_builder)
COMMAND_SEQUENCE = [
    # C2: Register Proforma → stays in REGISTRO
    ("C2", "REGISTRO", lambda exp: build_c2_payload(exp)),
    # C5: Confirm Registration → PRODUCCION
    ("C5", "PRODUCCION", lambda exp: build_production_payload(exp)),
    # C6: Finalize Production → PREPARACION
    ("C6", "PREPARACION", lambda exp: build_preparacion_payload(exp)),
    # C11: Confirm Customs Departure → TRANSITO (skipping DESPACHO for simplicity)
    ("C11", "TRANSITO", lambda exp: build_transito_payload(exp)),
    # C12: Confirm Arrival → EN_DESTINO
    ("C12", "EN_DESTINO", None),
    # C14: Close → CERRADO
    ("C14", "CERRADO", None),
]

# Map new status to its position in the command sequence
STATUS_ORDER = {
    "REGISTRO": 0,
    "PRODUCCION": 1,
    "PREPARACION": 2,
    "DESPACHO": 3,
    "TRANSITO": 3,  # same level as despacho in old system
    "EN_DESTINO": 4,
    "CERRADO": 5,
    "CANCELADO": -1,
}


def determine_target_status(old_status: str, exp: "OldExpediente | None" = None) -> str:
    """
    Map old status string to new ExpedienteStatus.

    Special case — "pagado":
      If despacho date is >100 days ago → CERRADO (confirmed paid).
      Otherwise → EN_DESTINO (still within payment window).
    """
    mapped = STATUS_MAP.get(old_status)
    if not mapped:
        # Fallback: try case-insensitive match
        for key, (new_status, _) in STATUS_MAP.items():
            if key.lower() == old_status.lower():
                mapped = (new_status, _)
                break
    if not mapped:
        return "REGISTRO"

    target = mapped[0]

    # Dynamic resolution for "pagado"
    if target == "_PAGADO_DYNAMIC" and exp:
        despacho_date = _extract_despacho_date(exp)
        if despacho_date:
            days_since = (datetime.now() - despacho_date).days
            if days_since > 100:
                log.info("    pagado: %d days since despacho → CERRADO", days_since)
                return "CERRADO"
            else:
                log.info("    pagado: %d days since despacho → EN_DESTINO", days_since)
                return "EN_DESTINO"
        else:
            # No despacho date available — assume CERRADO (safe default for "pagado")
            log.warning("    pagado: no despacho date found → defaulting to CERRADO")
            return "CERRADO"

    return target


def _extract_despacho_date(exp: "OldExpediente") -> datetime | None:
    """Extract despacho/shipping date from old expediente data."""
    # Try despacho.shipping.fechas first (despacho date)
    if exp.despacho and isinstance(exp.despacho, dict):
        data = exp.despacho.get("data", exp.despacho)
        shipping = data.get("shipping", {})
        for field in ("fechas", "fecha_arribo"):
            val = shipping.get(field)
            if val:
                try:
                    return datetime.strptime(val, "%Y-%m-%d")
                except ValueError:
                    continue
    # Fallback: try from raw data
    raw_despacho = exp.raw.get("listDespachoInfo")
    if raw_despacho and isinstance(raw_despacho, dict):
        data = raw_despacho.get("data", {})
        shipping = data.get("shipping", {})
        for field in ("fechas", "fecha_arribo"):
            val = shipping.get(field)
            if val:
                try:
                    return datetime.strptime(val, "%Y-%m-%d")
                except ValueError:
                    continue
    return None


def get_commands_to_execute(target_status: str) -> list[tuple[str, str, Any]]:
    """
    Return the subset of COMMAND_SEQUENCE needed to reach target_status.
    """
    target_order = STATUS_ORDER.get(target_status, 0)
    if target_order <= 0:
        return []
    commands = []
    for cmd_id, status, builder in COMMAND_SEQUENCE:
        cmd_order = STATUS_ORDER.get(status, 0)
        if cmd_order <= target_order:
            commands.append((cmd_id, status, builder))
        else:
            break
    return commands


# ---------------------------------------------------------------------------
# Migration Engine
# ---------------------------------------------------------------------------

class MigrationEngine:
    """Orchestrates the migration of expedientes from old to new system."""

    def __init__(
        self,
        old_client: OldApiClient,
        new_client: NewApiClient,
        client_map: dict,
        brand_id: str | None = None,
        dry_run: bool = False,
    ):
        self.old = old_client
        self.new = new_client
        self.client_map = client_map
        self.brand_id = brand_id
        self.dry_run = dry_run
        self.results: list[MigrationResult] = []

    def run(self, filter_order: str | None = None, limit: int | None = None):
        """Execute the full migration."""
        log.info("=" * 60)
        log.info("Starting migration%s", " (DRY RUN)" if self.dry_run else "")
        log.info("=" * 60)

        # Step 1: Get all orders from old system
        log.info("Fetching order list from old API...")
        orders = self.old.list_orders()
        log.info("Found %d orders in old system", len(orders))

        if not orders:
            log.warning("No orders found. Check API connectivity.")
            return

        # Filter if requested
        if filter_order:
            orders = [o for o in orders if o.get("order_number") == filter_order]
            log.info("Filtered to %d order(s) matching %s", len(orders), filter_order)

        if limit:
            orders = orders[:limit]
            log.info("Limited to first %d orders", limit)

        # Step 2: Check existing expedientes in new system to avoid duplicates
        existing = set()
        if not self.dry_run:
            log.info("Checking existing expedientes in new system...")
            for exp in self.new.list_expedientes():
                # Check metadata for original order number
                meta = exp.get("metadata", {}) or {}
                orig = meta.get("original_order_number")
                if orig:
                    existing.add(orig)
            log.info("Found %d already-migrated expedientes", len(existing))

        # Step 3: Process each order
        for i, order_summary in enumerate(orders, 1):
            order_number = order_summary.get("order_number", f"unknown-{i}")
            log.info("-" * 40)
            log.info("[%d/%d] Processing %s (status: %s)",
                     i, len(orders), order_number,
                     order_summary.get("order_status", "?"))

            # Skip duplicates
            if order_number in existing:
                result = MigrationResult(
                    order_number=order_number,
                    success=True,
                    skipped=True,
                    skip_reason="Already exists in new system",
                )
                self.results.append(result)
                log.info("  SKIPPED: already migrated")
                continue

            result = self._migrate_one(order_summary)
            self.results.append(result)

        # Summary
        self._print_summary()

    def _migrate_one(self, order_summary: dict) -> MigrationResult:
        """Migrate a single expediente."""
        order_number = order_summary.get("order_number", "")
        result = MigrationResult(order_number=order_number, success=False)

        try:
            # Fetch full detail from old system
            log.info("  Fetching full detail from old API...")
            exp = self.old.fetch_full_expediente(order_summary)

            # Determine target status in new system
            target_status = determine_target_status(exp.order_status, exp)
            log.info("  Old status: %s → New target: %s", exp.order_status, target_status)

            if self.dry_run:
                result.success = True
                result.commands_executed = ["DRY_RUN"]
                log.info("  DRY RUN: Would create expediente and advance to %s", target_status)
                self._save_dry_run_data(exp)
                return result

            # C1: Create expediente
            c1_payload = build_c1_payload(exp, self.client_map, self.brand_id)
            log.info("  Executing C1 (Create)...")
            c1_result = self.new.create_expediente(c1_payload)
            if not c1_result:
                result.errors.append("C1 (Create) failed")
                return result

            expediente_id = c1_result.get("expediente_id") or c1_result.get("id")
            if not expediente_id:
                result.errors.append(f"C1 succeeded but no ID returned: {c1_result}")
                return result

            result.new_expediente_id = str(expediente_id)
            result.commands_executed.append("C1")
            log.info("  Created expediente %s", expediente_id)

            # Execute command sequence to reach target status
            if target_status == "CANCELADO":
                # Special case: create then cancel
                cancel_result = self.new.execute_command(
                    expediente_id, "CANCEL",
                    {"reason": f"Migrated as cancelled from {order_number}"},
                )
                if cancel_result:
                    result.commands_executed.append("CANCEL")
                else:
                    result.errors.append("CANCEL command failed")
            else:
                commands = get_commands_to_execute(target_status)
                for cmd_id, _, payload_builder in commands:
                    payload = {}
                    if payload_builder:
                        built = payload_builder(exp)
                        if built:
                            payload = built

                    log.info("  Executing %s...", cmd_id)
                    cmd_result = self.new.execute_command(expediente_id, cmd_id, payload)
                    if cmd_result:
                        result.commands_executed.append(cmd_id)
                    else:
                        result.errors.append(f"{cmd_id} failed")
                        log.warning("  Command %s failed, stopping sequence", cmd_id)
                        break

            # Register payments if available
            payment_payloads = build_payment_payloads(exp)
            for pay_payload in payment_payloads:
                log.info("  Registering payment (C21)...")
                pay_result = self.new.execute_command(expediente_id, "C21", pay_payload)
                if pay_result:
                    result.commands_executed.append("C21")
                else:
                    result.errors.append("C21 (payment) failed")

            result.success = len(result.errors) == 0
            status_label = "OK" if result.success else "PARTIAL"
            log.info("  %s — commands: %s", status_label, ", ".join(result.commands_executed))

        except Exception as e:
            result.errors.append(f"Unexpected error: {e}")
            log.exception("  Error migrating %s", order_number)

        return result

    def _save_dry_run_data(self, exp: OldExpediente):
        """Save fetched data to disk during dry run for inspection."""
        output_dir = Path("data/migration_dry_run")
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{exp.order_number}.json"
        data = {
            "order_number": exp.order_number,
            "order_status": exp.order_status,
            "customer_name": exp.customer_name,
            "order_full_price": exp.order_full_price,
            "order_created_date": exp.order_created_date,
            "number_purchase": exp.number_purchase,
            "operado_mwt": exp.operado_mwt,
            "target_status": determine_target_status(exp.order_status, exp),
            "commands_needed": [
                cmd for cmd, _, _ in get_commands_to_execute(
                    determine_target_status(exp.order_status, exp)
                )
            ],
            "raw_data": exp.raw,
        }
        filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))
        log.info("  Saved dry run data to %s", filepath)

    def _print_summary(self):
        """Print migration summary."""
        total = len(self.results)
        success = sum(1 for r in self.results if r.success and not r.skipped)
        skipped = sum(1 for r in self.results if r.skipped)
        failed = sum(1 for r in self.results if not r.success)
        partial = sum(1 for r in self.results if r.success and r.errors)

        log.info("=" * 60)
        log.info("MIGRATION SUMMARY")
        log.info("=" * 60)
        log.info("Total:    %d", total)
        log.info("Success:  %d", success)
        log.info("Skipped:  %d (already existed)", skipped)
        log.info("Partial:  %d (created but not fully advanced)", partial)
        log.info("Failed:   %d", failed)

        if failed > 0:
            log.info("")
            log.info("FAILED ORDERS:")
            for r in self.results:
                if not r.success:
                    log.info("  %s: %s", r.order_number, "; ".join(r.errors))

        # Save full report
        report_path = Path("data/migration_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "success": success,
                "skipped": skipped,
                "partial": partial,
                "failed": failed,
            },
            "results": [
                {
                    "order_number": r.order_number,
                    "success": r.success,
                    "new_expediente_id": r.new_expediente_id,
                    "commands_executed": r.commands_executed,
                    "errors": r.errors,
                    "skipped": r.skipped,
                    "skip_reason": r.skip_reason,
                }
                for r in self.results
            ],
        }
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        log.info("Full report saved to %s", report_path)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_float(val) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _is_error_response(data: dict) -> bool:
    """Check if the API response indicates an error."""
    if data.get("error"):
        return True
    if data.get("status") in ("error", "fail", "403", "404"):
        return True
    if data.get("message", "").lower().startswith("error"):
        return True
    return False


def load_client_map(path: str | None) -> dict:
    """
    Load mapping from old customer names/IDs to new system LegalEntity PKs.

    Expected format (JSON):
    {
        "Customer Name Old": <new_legal_entity_pk>,
        "12": <new_legal_entity_pk>
    }
    """
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        log.warning("Client map file not found: %s", path)
        return {}
    return json.loads(p.read_text())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migrate expedientes from old PHP API to new Django system"
    )
    parser.add_argument("--dry-run", action="store_true",
                        help="Fetch from old API but don't write to new system")
    parser.add_argument("--order", type=str, default=None,
                        help="Migrate only this order number (e.g. MWT-0028-2025)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of orders to process")
    parser.add_argument("--new-api-url", type=str, default=NEW_API_BASE,
                        help=f"New API base URL (default: {NEW_API_BASE})")
    parser.add_argument("--token", type=str, default="",
                        help="Auth token for the new Django API")
    parser.add_argument("--client-map", type=str, default=None,
                        help="Path to JSON file mapping old customers to new LegalEntity PKs")
    parser.add_argument("--brand-id", type=str, default=None,
                        help="Brand PK in new system to assign to all migrated expedientes")
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY,
                        help=f"Delay between old API requests in seconds (default: {REQUEST_DELAY})")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    import os
    token = args.token or os.environ.get("MWT_API_TOKEN", "")

    if not args.dry_run and not token:
        log.error("No auth token provided. Use --token or set MWT_API_TOKEN env var.")
        log.error("Use --dry-run to test without the new API.")
        sys.exit(1)

    old_client = OldApiClient(OLD_API_BASE, OLD_API_AUTH, delay=args.delay)
    new_client = NewApiClient(args.new_api_url, token)
    client_map = load_client_map(args.client_map)

    engine = MigrationEngine(
        old_client=old_client,
        new_client=new_client,
        client_map=client_map,
        brand_id=args.brand_id,
        dry_run=args.dry_run,
    )
    engine.run(filter_order=args.order, limit=args.limit)


if __name__ == "__main__":
    main()
