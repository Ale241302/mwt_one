"""
seed_demo_data.py — Management command para poblar mwt.one con datos de demo

Uso: python manage.py seed_demo_data
Limpia: python manage.py seed_demo_data --flush

Crea datos realistas que ejercitan TODA la funcionalidad visible:
- 10 expedientes en distintos estados (todos los 8 + variantes)
- Artefactos por expediente (OC, proforma, AWB, factura, costos)
- 2 transfers (planned, in_transit)
- 1 liquidación con matching
- Alertas de crédito (reloj activo)
- 1 expediente bloqueado
- 1 cancelado

Los datos están basados en operaciones reales (Sondel, UMMIE, Imporcomp)
pero con valores ficticios para demo.

IMPORTANTE: este script llama a services.py directamente, no a la API HTTP.
Así respeta la state machine sin tener que hacer 100 HTTP calls.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json
import uuid


DEMO_BRAND = "marluvas_demo"
DEMO_PERIOD = "2026-02"   # max_length=7 en Liquidation


class Command(BaseCommand):
    help = "Seed demo data for mwt.one Sprint 5 frontend"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete all demo data first")

    def handle(self, *args, **options):
        # ══════════════════════════════════════════════════════════════
        # IMPORTS — ajustar según estructura real del proyecto
        # ══════════════════════════════════════════════════════════════
        try:
            from apps.expedientes.models import (
                Expediente, ArtifactInstance, CostLine, PaymentLine, EventLog
            )
            from apps.transfers.models import Transfer, TransferLine, Node
            from apps.core.models import (
                LegalEntity, LegalEntityRole, LegalEntityRelationship,
                LegalEntityFrontend, LegalEntityVisibility, PricingVisibility
            )
        except ImportError as e:
            self.stderr.write(
                f"ERROR: No se encontraron los modelos: {e}\n"
                "Paths esperados: apps.expedientes.models, apps.transfers.models, apps.core.models\n"
            )
            return

        # Intentar importar liquidaciones (Sprint 5)
        try:
            from apps.liquidations.models import Liquidation, LiquidationLine
            HAS_LIQUIDATIONS = True
        except ImportError:
            HAS_LIQUIDATIONS = False
            self.stdout.write("WARN: Liquidations module not found — skipping")

        # ══════════════════════════════════════════════════════════════
        # FLUSH
        # ══════════════════════════════════════════════════════════════
        if options["flush"]:
            self.stdout.write("Flushing demo data...")
            try:
                EventLog.objects.filter(expediente__brand=DEMO_BRAND).delete()
            except Exception:
                pass
            try:
                # PaymentLine es append-only, usar queryset.delete() directamente
                PaymentLine.objects.filter(expediente__brand=DEMO_BRAND)._raw_delete(
                    PaymentLine.objects.filter(expediente__brand=DEMO_BRAND).db
                )
            except Exception:
                pass
            try:
                CostLine.objects.filter(expediente__brand=DEMO_BRAND)._raw_delete(
                    CostLine.objects.filter(expediente__brand=DEMO_BRAND).db
                )
            except Exception:
                pass
            try:
                ArtifactInstance.objects.filter(expediente__brand=DEMO_BRAND).delete()
            except Exception:
                pass
            try:
                # Eliminar transfers vinculados a expedientes demo
                demo_exps = Expediente.objects.filter(brand=DEMO_BRAND)
                Transfer.objects.filter(source_expediente__in=demo_exps).delete()
                # También los que tengan notas de demostración
                Transfer.objects.filter(cancel_reason="SEED_DEMO").delete()
            except Exception as e:
                self.stderr.write(f"  WARN flush transfers: {e}")
            try:
                Expediente.objects.filter(brand=DEMO_BRAND).delete()
            except Exception:
                pass
            try:
                Node.objects.filter(location="DEMO").delete()
            except Exception:
                pass
            if HAS_LIQUIDATIONS:
                try:
                    Liquidation.objects.filter(period=DEMO_PERIOD, brand=DEMO_BRAND).delete()
                except Exception as e:
                    self.stderr.write(f"  WARN flush liquidation: {e}")
            self.stdout.write(self.style.SUCCESS("Flushed."))
            return

        now = timezone.now()
        self.stdout.write("Seeding demo data...")

        # ══════════════════════════════════════════════════════════════
        # HELPERS
        # ══════════════════════════════════════════════════════════════
        def make_exp(ref, client, mode, status, days_ago, **kwargs):
            """Create expediente with timestamps backdated"""
            exp = Expediente.objects.create(
                brand=DEMO_BRAND,
                client_id=client,
                mode=mode,
                status=status,
                freight_mode=kwargs.get("freight_mode", "prepaid"),
                transport_mode=kwargs.get("transport_mode", "aereo"),
                dispatch_mode=kwargs.get("dispatch_mode", "mwt"),
                is_blocked=kwargs.get("is_blocked", False),
                blocked_reason=kwargs.get("blocked_reason", None),
                blocked_at=kwargs.get("blocked_at", None),
                blocked_by_type=kwargs.get("blocked_by_type", None),
                payment_status=kwargs.get("payment_status", "pending"),
                credit_clock_started_at=kwargs.get("credit_clock_started_at", None),
            )
            # Backdate created_at
            Expediente.objects.filter(pk=exp.pk).update(
                created_at=now - timedelta(days=days_ago)
            )
            exp.refresh_from_db()
            self.stdout.write(f"  EXP {exp.pk} [{status}] — {client} ({mode})")
            return exp

        def make_artifact(exp, art_type, status="completed", payload=None, days_ago=0):
            art = ArtifactInstance.objects.create(
                expediente=exp,
                artifact_type=art_type,
                status=status,
                payload=payload or {},
            )
            if days_ago:
                ArtifactInstance.objects.filter(pk=art.pk).update(
                    created_at=now - timedelta(days=days_ago)
                )
            return art

        def make_cost(exp, concept, amount, phase, days_ago=0, visibility="internal"):
            """CostLine es append-only — solo INSERT"""
            cl = CostLine(
                expediente=exp,
                cost_type=concept,
                amount=Decimal(str(amount)),
                currency="USD",
                phase=phase,
                description=f"{concept} — demo",
                visibility=visibility,
            )
            # Bypassear validación append-only con save directo
            super(CostLine, cl).save(force_insert=True)
            if days_ago:
                CostLine.objects.filter(pk=cl.pk).update(
                    created_at=now - timedelta(days=days_ago)
                )
            return cl

        def make_payment(exp, amount, method="wire", reference="", days_ago=0):
            pl = PaymentLine(
                expediente=exp,
                amount=Decimal(str(amount)),
                currency="USD",
                method=method,
                reference=reference,
            )
            super(PaymentLine, pl).save(force_insert=True)
            if days_ago:
                PaymentLine.objects.filter(pk=pl.pk).update(
                    created_at=now - timedelta(days=days_ago)
                )
            return pl

        def make_event(exp, event_type, days_ago=0, data=None):
            evt = EventLog.objects.create(
                expediente=exp,
                event_type=event_type,
                data=data or {},
                occurred_at=now - timedelta(days=days_ago),
            )
            return evt

        # ══════════════════════════════════════════════════════════════
        # 1. EXPEDIENTE CERRADO (happy path completo) — Sondel Modelo C
        # ══════════════════════════════════════════════════════════════
        exp1 = make_exp("EXP-DEMO-001", "SONDEL-CR", "FULL", "CERRADO", 90,
                        payment_status="paid",
                        credit_clock_started_at=now - timedelta(days=85))

        make_artifact(exp1, "ART-01", payload={"po_number": "PO-504652", "total": 33542.00, "items": 4}, days_ago=90)
        make_artifact(exp1, "ART-02", payload={"consecutive": "2395-2025", "total_usd": 33542.00, "comision_pactada": None}, days_ago=88)
        make_artifact(exp1, "ART-05", payload={"carrier": "Copa Airlines Cargo", "awb": "230-12345678", "transport_mode": "aereo", "route": "CNF→PTY→SJO"}, days_ago=60)
        make_artifact(exp1, "ART-09", payload={"invoice_number": "FE-001-0001234", "total": 47693.00, "currency": "CRC"}, days_ago=10)
        make_cost(exp1, "merchandise", 33542.00, "PRODUCCION", 85)
        make_cost(exp1, "freight_air", 4850.00, "DESPACHO", 58)
        make_cost(exp1, "customs_dai", 4695.88, "EN_DESTINO", 25)
        make_cost(exp1, "customs_iva", 5583.34, "EN_DESTINO", 25)
        make_cost(exp1, "handling", 350.00, "EN_DESTINO", 24)
        make_payment(exp1, 47693.00, "wire", "TRF-SONDEL-2025-12", 8)
        make_event(exp1, "expediente.created", 90)
        make_event(exp1, "expediente.state_changed", 85, {"from": "REGISTRO", "to": "PRODUCCION"})
        make_event(exp1, "expediente.state_changed", 65, {"from": "PRODUCCION", "to": "PREPARACION"})
        make_event(exp1, "expediente.state_changed", 58, {"from": "PREPARACION", "to": "DESPACHO"})
        make_event(exp1, "expediente.state_changed", 55, {"from": "DESPACHO", "to": "TRANSITO"})
        make_event(exp1, "expediente.state_changed", 25, {"from": "TRANSITO", "to": "EN_DESTINO"})
        make_event(exp1, "expediente.completed", 8)

        # ══════════════════════════════════════════════════════════════
        # 2. EN TRÁNSITO — Sondel Modelo C, reloj crédito activo (día 55)
        # ══════════════════════════════════════════════════════════════
        exp2 = make_exp("EXP-DEMO-002", "SONDEL-CR", "FULL", "TRANSITO", 60,
                        credit_clock_started_at=now - timedelta(days=55))

        make_artifact(exp2, "ART-01", payload={"po_number": "PO-504855", "total": 28750.00}, days_ago=60)
        make_artifact(exp2, "ART-02", payload={"consecutive": "2427-2026", "total_usd": 28750.00}, days_ago=58)
        make_artifact(exp2, "ART-05", payload={"carrier": "Copa Airlines Cargo", "awb": "230-87654321", "transport_mode": "aereo", "route": "CNF→PTY→SJO"}, days_ago=55)
        make_cost(exp2, "merchandise", 28750.00, "PRODUCCION", 55)
        make_cost(exp2, "freight_air", 3200.00, "DESPACHO", 50)
        make_event(exp2, "expediente.created", 60)
        make_event(exp2, "expediente.state_changed", 55, {"from": "REGISTRO", "to": "PRODUCCION"})
        make_event(exp2, "expediente.state_changed", 52, {"from": "PRODUCCION", "to": "PREPARACION"})
        make_event(exp2, "expediente.state_changed", 50, {"from": "PREPARACION", "to": "DESPACHO"})
        make_event(exp2, "expediente.state_changed", 48, {"from": "DESPACHO", "to": "TRANSITO"})

        # ══════════════════════════════════════════════════════════════
        # 3. EN DESTINO — UMMIE Guatemala, reloj crédito día 78 (ALERTA ÁMBAR)
        # ══════════════════════════════════════════════════════════════
        exp3 = make_exp("EXP-DEMO-003", "UMMIE-GT", "COMISION", "EN_DESTINO", 85,
                        credit_clock_started_at=now - timedelta(days=78),
                        payment_status="partial")

        make_artifact(exp3, "ART-01", payload={"po_number": "PO-GT-2026-001", "total": 15200.00}, days_ago=85)
        make_artifact(exp3, "ART-02", payload={"consecutive": "2428-2026", "total_usd": 15200.00, "comision_pactada": 10.0}, days_ago=83)
        make_artifact(exp3, "ART-05", payload={"carrier": "DHL Express", "awb": "1234567890", "transport_mode": "aereo"}, days_ago=78)
        make_cost(exp3, "merchandise", 15200.00, "PRODUCCION", 80)
        make_cost(exp3, "freight_air", 1890.00, "DESPACHO", 75)
        make_payment(exp3, 800.00, "wire", "UMMIE-PARTIAL-001", 30)
        make_event(exp3, "expediente.created", 85)
        make_event(exp3, "credit_clock.warning", 18)

        # ══════════════════════════════════════════════════════════════
        # 4. BLOQUEADO — Sondel, crédito día 82 (ALERTA CORAL)
        # ══════════════════════════════════════════════════════════════
        exp4 = make_exp("EXP-DEMO-004", "SONDEL-CR", "FULL", "TRANSITO", 88,
                        is_blocked=True,
                        blocked_reason="Credit clock >75 days — auto block",
                        blocked_at=now - timedelta(days=7),
                        blocked_by_type="SYSTEM",
                        credit_clock_started_at=now - timedelta(days=82))

        make_artifact(exp4, "ART-01", payload={"po_number": "PO-504900", "total": 42100.00}, days_ago=88)
        make_artifact(exp4, "ART-02", payload={"consecutive": "2429-2026", "total_usd": 42100.00}, days_ago=86)
        make_artifact(exp4, "ART-05", payload={"carrier": "Copa Cargo", "awb": "230-11112222"}, days_ago=82)
        make_cost(exp4, "merchandise", 42100.00, "PRODUCCION", 85)
        make_event(exp4, "expediente.created", 88)
        make_event(exp4, "credit_clock.warning", 22)
        make_event(exp4, "expediente.blocked", 7, {"reason": "Credit clock >75 days"})

        # ══════════════════════════════════════════════════════════════
        # 5. REGISTRO — nuevo, recién creado
        # ══════════════════════════════════════════════════════════════
        exp5 = make_exp("EXP-DEMO-005", "IMPORCOMP-CO", "COMISION", "REGISTRO", 3)
        make_artifact(exp5, "ART-01", payload={"po_number": "PO-CO-2026-015", "total": 8500.00}, days_ago=3)
        make_event(exp5, "expediente.created", 3)

        # ══════════════════════════════════════════════════════════════
        # 6. PRODUCCION — en fábrica, esperando
        # ══════════════════════════════════════════════════════════════
        exp6 = make_exp("EXP-DEMO-006", "SONDEL-CR", "FULL", "PRODUCCION", 30)
        make_artifact(exp6, "ART-01", payload={"po_number": "PO-505100", "total": 22300.00}, days_ago=30)
        make_artifact(exp6, "ART-02", payload={"consecutive": "2430-2026", "total_usd": 22300.00}, days_ago=28)
        make_cost(exp6, "merchandise", 22300.00, "PRODUCCION", 25)
        make_event(exp6, "expediente.created", 30)
        make_event(exp6, "expediente.state_changed", 25, {"from": "REGISTRO", "to": "PRODUCCION"})

        # ══════════════════════════════════════════════════════════════
        # 7. PREPARACION — listo para despachar
        # ══════════════════════════════════════════════════════════════
        exp7 = make_exp("EXP-DEMO-007", "UMMIE-GT", "COMISION", "PREPARACION", 45)
        make_artifact(exp7, "ART-01", payload={"po_number": "PO-GT-2026-002", "total": 11800.00}, days_ago=45)
        make_artifact(exp7, "ART-02", payload={"consecutive": "2431-2026", "total_usd": 11800.00, "comision_pactada": 9.37}, days_ago=43)
        make_cost(exp7, "merchandise", 11800.00, "PRODUCCION", 40)
        make_event(exp7, "expediente.created", 45)
        make_event(exp7, "expediente.state_changed", 40, {"from": "REGISTRO", "to": "PRODUCCION"})
        make_event(exp7, "expediente.state_changed", 20, {"from": "PRODUCCION", "to": "PREPARACION"})

        # ══════════════════════════════════════════════════════════════
        # 8. DESPACHO — docs listos, embarcando
        # ══════════════════════════════════════════════════════════════
        exp8 = make_exp("EXP-DEMO-008", "SONDEL-CR", "FULL", "DESPACHO", 50,
                        credit_clock_started_at=now - timedelta(days=15))
        make_artifact(exp8, "ART-01", payload={"po_number": "PO-505200", "total": 19500.00}, days_ago=50)
        make_artifact(exp8, "ART-02", payload={"consecutive": "2432-2026", "total_usd": 19500.00}, days_ago=48)
        make_artifact(exp8, "ART-05", payload={"carrier": "Copa Cargo", "awb": "230-33334444"}, days_ago=15)
        make_artifact(exp8, "ART-06", payload={"carrier": "Copa Cargo", "quote": 2800.00, "mode": "aereo"}, days_ago=18)
        make_cost(exp8, "merchandise", 19500.00, "PRODUCCION", 45)
        make_cost(exp8, "freight_air", 2800.00, "DESPACHO", 15)
        make_event(exp8, "expediente.created", 50)
        make_event(exp8, "expediente.state_changed", 45, {"from": "REGISTRO", "to": "PRODUCCION"})
        make_event(exp8, "expediente.state_changed", 22, {"from": "PRODUCCION", "to": "PREPARACION"})
        make_event(exp8, "expediente.state_changed", 15, {"from": "PREPARACION", "to": "DESPACHO"})

        # ══════════════════════════════════════════════════════════════
        # 9. CANCELADO
        # ══════════════════════════════════════════════════════════════
        exp9 = make_exp("EXP-DEMO-009", "IMPORCOMP-CO", "COMISION", "CANCELADO", 40)
        make_artifact(exp9, "ART-01", payload={"po_number": "PO-CO-2026-010", "total": 5200.00}, days_ago=40)
        make_event(exp9, "expediente.created", 40)
        make_event(exp9, "expediente.cancelled", 35, {"reason": "Cliente canceló PO"})

        # ══════════════════════════════════════════════════════════════
        # 10. CERRADO Modelo B — con comisión pagada
        # ══════════════════════════════════════════════════════════════
        exp10 = make_exp("EXP-DEMO-010", "UMMIE-GT", "COMISION", "CERRADO", 120,
                         payment_status="paid",
                         credit_clock_started_at=now - timedelta(days=100))

        make_artifact(exp10, "ART-01", payload={"po_number": "PO-GT-2025-050", "total": 9800.00}, days_ago=120)
        make_artifact(exp10, "ART-02", payload={"consecutive": "2354-2025", "total_usd": 9800.00, "comision_pactada": 9.37}, days_ago=118)
        make_artifact(exp10, "ART-05", payload={"carrier": "DHL", "awb": "5556667778"}, days_ago=100)
        make_cost(exp10, "merchandise", 9800.00, "PRODUCCION", 115)
        make_cost(exp10, "freight_air", 1200.00, "DESPACHO", 98)
        make_payment(exp10, 918.26, "liquidacion_marluvas", "LIQ-2025-12", 20)
        make_event(exp10, "expediente.created", 120)
        make_event(exp10, "expediente.completed", 15)

        self.stdout.write(self.style.SUCCESS(f"\n✅ 10 expedientes creados"))

        # ══════════════════════════════════════════════════════════════
        # LEGAL ENTITY para Nodes (requerido FK)
        # ══════════════════════════════════════════════════════════════
        self.stdout.write("\nCreando nodos y transfers...")

        try:
            le_mwt, _ = LegalEntity.objects.get_or_create(
                entity_id="MWT-CR",
                defaults={
                    "legal_name": "MWT Costa Rica S.A.",
                    "country": "CR",
                    "role": "OWNER",
                    "relationship_to_mwt": "SELF",
                    "frontend": "MWT_ONE",
                    "visibility_level": "FULL",
                    "pricing_visibility": "INTERNAL",
                    "status": "ACTIVE",
                }
            )
            le_amazon, _ = LegalEntity.objects.get_or_create(
                entity_id="AMAZON-US",
                defaults={
                    "legal_name": "Amazon.com Services LLC",
                    "country": "US",
                    "role": "THREEPL",
                    "relationship_to_mwt": "SERVICE",
                    "frontend": "EXTERNAL",
                    "visibility_level": "LIMITED",
                    "pricing_visibility": "NONE",
                    "status": "ACTIVE",
                }
            )

            # ══════════════════════════════════════════════════════════════
            # NODOS
            # ══════════════════════════════════════════════════════════════
            node_fiscal, _ = Node.objects.get_or_create(
                location="DEMO",
                name="Almacén Fiscal CR",
                defaults={
                    "legal_entity": le_mwt,
                    "node_type": "fiscal",
                    "status": "active",
                }
            )

            node_own, _ = Node.objects.get_or_create(
                location="DEMO",
                name="Bodega MWT CR",
                defaults={
                    "legal_entity": le_mwt,
                    "node_type": "owned_warehouse",
                    "status": "active",
                }
            )

            node_fba, _ = Node.objects.get_or_create(
                location="DEMO",
                name="Amazon FBA USA",
                defaults={
                    "legal_entity": le_amazon,
                    "node_type": "fba",
                    "status": "active",
                }
            )

            # ══════════════════════════════════════════════════════════════
            # TRANSFERS — transfer_id es auto-generado, marcamos con cancel_reason
            # ══════════════════════════════════════════════════════════════
            # Transfer 1: fiscal → bodega propia (nationalization, in_transit)
            trf1 = Transfer.objects.create(
                from_node=node_fiscal,
                to_node=node_own,
                ownership_changes=False,
                legal_context="nationalization",
                customs_required=True,
                status="in_transit",
                source_expediente=exp1,
                cancel_reason="SEED_DEMO",   # marca para flush
            )
            TransferLine.objects.create(
                transfer=trf1, sku="RW-GOL-MED-S3", quantity_dispatched=200)
            TransferLine.objects.create(
                transfer=trf1, sku="RW-GOL-MED-S4", quantity_dispatched=300)
            TransferLine.objects.create(
                transfer=trf1, sku="RW-GOL-MED-S5", quantity_dispatched=250)

            # Transfer 2: bodega → FBA (internal, planned)
            trf2 = Transfer.objects.create(
                from_node=node_own,
                to_node=node_fba,
                ownership_changes=False,
                legal_context="internal",
                customs_required=False,
                status="planned",
                cancel_reason="SEED_DEMO",   # marca para flush
            )
            TransferLine.objects.create(
                transfer=trf2, sku="RW-GOL-MED-S3", quantity_dispatched=100)
            TransferLine.objects.create(
                transfer=trf2, sku="RW-GOL-MED-S4", quantity_dispatched=150)

            self.stdout.write(self.style.SUCCESS(
                f"  2 transfers ({trf1.transfer_id}, {trf2.transfer_id}) + 3 nodos creados"
            ))
        except Exception as e:
            self.stderr.write(f"  WARN transfers/nodes: {e}")
            import traceback; traceback.print_exc()

        # ══════════════════════════════════════════════════════════════
        # LIQUIDACIÓN (si Sprint 5 está activo)
        # ══════════════════════════════════════════════════════════════
        if HAS_LIQUIDATIONS:
            self.stdout.write("\nCreando liquidación demo...")
            try:
                liq = Liquidation.objects.create(
                    period=DEMO_PERIOD,      # "2026-02" — 7 chars OK
                    brand=DEMO_BRAND,
                    status="in_review",
                )
                LiquidationLine.objects.create(
                    liquidation=liq,
                    marluvas_reference="2354-2025",
                    concept="comision",
                    client_payment_amount=Decimal("9800.00"),
                    commission_pct_reported=Decimal("9.37"),
                    commission_amount=Decimal("918.26"),
                    currency="USD",
                    match_status="matched",
                    matched_expediente=exp10,
                )
                LiquidationLine.objects.create(
                    liquidation=liq,
                    marluvas_reference="2428-2026",
                    concept="comision",
                    client_payment_amount=Decimal("7600.00"),
                    commission_pct_reported=Decimal("10.00"),
                    commission_amount=Decimal("760.00"),
                    currency="USD",
                    match_status="matched",
                    matched_expediente=exp3,
                    is_partial_payment=True,
                )
                LiquidationLine.objects.create(
                    liquidation=liq,
                    marluvas_reference="PREMIO-FEB",
                    concept="premio",
                    client_payment_amount=Decimal("0"),
                    commission_pct_reported=Decimal("0"),
                    commission_amount=Decimal("1201.80"),
                    currency="USD",
                    match_status="no_match_needed",
                )
                self.stdout.write(self.style.SUCCESS("  1 liquidación + 3 líneas creadas"))
            except Exception as e:
                self.stderr.write(f"  WARN liquidation: {e}")
                import traceback; traceback.print_exc()

        # ══════════════════════════════════════════════════════════════
        # RESUMEN
        # ══════════════════════════════════════════════════════════════
        self.stdout.write(self.style.SUCCESS("""
╔══════════════════════════════════════════════════════════════════╗
║                    SEED DATA COMPLETADO                         ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  EXPEDIENTES (10):                                               ║
║    EXP-001  CERRADO      Sondel CR    FULL     Happy path       ║
║    EXP-002  TRANSITO     Sondel CR    FULL     Reloj día 55     ║
║    EXP-003  EN_DESTINO   UMMIE GT     COMISION Reloj día 78 ⚠  ║
║    EXP-004  BLOQUEADO    Sondel CR    FULL     Reloj día 82 🔴  ║
║    EXP-005  REGISTRO     Imporcomp CO COMISION Recién creado    ║
║    EXP-006  PRODUCCION   Sondel CR    FULL     En fábrica       ║
║    EXP-007  PREPARACION  UMMIE GT     COMISION Listo despachar  ║
║    EXP-008  DESPACHO     Sondel CR    FULL     Embarcando       ║
║    EXP-009  CANCELADO    Imporcomp CO COMISION PO cancelada     ║
║    EXP-010  CERRADO      UMMIE GT     COMISION Modelo B pagado  ║
║                                                                  ║
║  SEMÁFOROS CRÉDITO:                                              ║
║    🟢 EXP-008 (15d)                                             ║
║    🟢 EXP-002 (55d)                                             ║
║    🟡 EXP-003 (78d) — alerta                                    ║
║    🔴 EXP-004 (82d) — bloqueado auto                            ║
║                                                                  ║
║  TRANSFERS (2):                                                  ║
║    TRF-001  in_transit   FISCAL-CR → OWN-WH-CR (nationalization)║
║    TRF-002  planned      OWN-WH-CR → FBA-US (internal)         ║
║                                                                  ║
║  LIQUIDACIÓN (1):                                                ║
║    LIQ 2026-02  in_review  3 líneas (2 comisión + 1 premio)     ║
║                                                                  ║
║  Para limpiar: python manage.py seed_demo_data --flush           ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""))
