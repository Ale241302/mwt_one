"""
seed_demo_data.py — Management command para poblar mwt.one con datos de demo

Uso:    python manage.py seed_demo_data
Limpia: python manage.py seed_demo_data --flush
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal


class Command(BaseCommand):
    help = "Seed demo data for mwt.one"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete all demo data first")

    def handle(self, *args, **options):
        try:
            from apps.expedientes.models import (
                Expediente, ArtifactInstance, CostLine, PaymentLine, EventLog
            )
        except ImportError as e:
            self.stderr.write(f"ERROR importando modelos: {e}")
            return

        try:
            from apps.transfers.models import Transfer, TransferLine, Node
            HAS_TRANSFERS = True
        except ImportError:
            HAS_TRANSFERS = False
            self.stdout.write("WARN: transfers module not found — skipping")

        try:
            from apps.liquidations.models import Liquidation, LiquidationLine
            HAS_LIQUIDATIONS = True
        except ImportError:
            HAS_LIQUIDATIONS = False
            self.stdout.write("WARN: Liquidations module not found — skipping")

        # ── FLUSH ──────────────────────────────────────────────────────
        if options["flush"]:
            self.stdout.write("Flushing demo data...")
            demo_exps = Expediente.objects.filter(brand="marluvas_demo")
            EventLog.objects.filter(expediente__in=demo_exps).delete()
            PaymentLine.objects.filter(expediente__in=demo_exps).delete()
            CostLine.objects.filter(expediente__in=demo_exps).delete()
            ArtifactInstance.objects.filter(expediente__in=demo_exps).delete()
            demo_exps.delete()
            if HAS_TRANSFERS:
                TransferLine.objects.filter(transfer__transfer_id__startswith="TRF-DEMO").delete()
                Transfer.objects.filter(transfer_id__startswith="TRF-DEMO").delete()
                Node.objects.filter(node_id__startswith="DEMO-").delete()
            if HAS_LIQUIDATIONS:
                liq_qs = Liquidation.objects.filter(period__startswith="DEMO")
                LiquidationLine.objects.filter(liquidation__in=liq_qs).delete()
                liq_qs.delete()
            self.stdout.write(self.style.SUCCESS("Flushed."))
            return

        now = timezone.now()
        self.stdout.write("Seeding demo data...")

        # ── HELPERS ────────────────────────────────────────────────────
        def make_exp(client, mode, status, days_ago, **kwargs):
            exp = Expediente.objects.create(
                brand="marluvas_demo",
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
            Expediente.objects.filter(pk=exp.pk).update(
                created_at=now - timedelta(days=days_ago)
            )
            exp.refresh_from_db()
            self.stdout.write(f"  EXP {exp.pk} [{status}] — {client}")
            return exp

        def make_artifact(exp, art_type, payload=None, days_ago=0):
            art = ArtifactInstance.objects.create(
                expediente=exp,
                artifact_type=art_type,
                status="completed",
                payload=payload or {},
            )
            if days_ago:
                ArtifactInstance.objects.filter(pk=art.pk).update(
                    created_at=now - timedelta(days=days_ago)
                )
            return art

        def make_cost(exp, concept, amount, phase, days_ago=0):
            cl = CostLine.objects.create(
                expediente=exp,
                cost_type=concept,
                amount=Decimal(str(amount)),
                currency="USD",
                phase=phase,
                description=f"{concept} — demo",
            )
            if days_ago:
                CostLine.objects.filter(pk=cl.pk).update(
                    created_at=now - timedelta(days=days_ago)
                )
            return cl

        def make_payment(exp, amount, method="wire", reference="", days_ago=0):
            pl = PaymentLine.objects.create(
                expediente=exp,
                amount=Decimal(str(amount)),
                currency="USD",
                method=method,
                reference=reference,
            )
            if days_ago:
                PaymentLine.objects.filter(pk=pl.pk).update(
                    created_at=now - timedelta(days=days_ago)
                )
            return pl

        def make_event(exp, event_type, days_ago=0, data=None):
            return EventLog.objects.create(
                expediente=exp,
                event_type=event_type,
                data=data or {},
                occurred_at=now - timedelta(days=days_ago),
            )

        # ── EXPEDIENTES ────────────────────────────────────────────────

        # 1. CERRADO — happy path
        exp1 = make_exp("SONDEL-CR", "FULL", "CERRADO", 90,
                        payment_status="paid",
                        credit_clock_started_at=now - timedelta(days=85))
        make_artifact(exp1, "ART-01", {"po_number": "PO-504652", "total": 33542.00}, 90)
        make_artifact(exp1, "ART-02", {"consecutive": "2395-2025", "total_usd": 33542.00}, 88)
        make_artifact(exp1, "ART-05", {"carrier": "Copa Cargo", "awb": "230-12345678"}, 60)
        make_artifact(exp1, "ART-09", {"invoice_number": "FE-001-0001234", "total": 47693.00}, 10)
        make_cost(exp1, "merchandise", 33542.00, "PRODUCCION", 85)
        make_cost(exp1, "freight_air", 4850.00, "DESPACHO", 58)
        make_cost(exp1, "customs_dai", 4695.88, "EN_DESTINO", 25)
        make_cost(exp1, "customs_iva", 5583.34, "EN_DESTINO", 25)
        make_cost(exp1, "handling", 350.00, "EN_DESTINO", 24)
        make_payment(exp1, 47693.00, "wire", "TRF-SONDEL-2025-12", 8)
        make_event(exp1, "expediente.created", 90)
        make_event(exp1, "expediente.state_changed", 58, {"from": "PREPARACION", "to": "DESPACHO"})
        make_event(exp1, "expediente.completed", 8)

        # 2. TRANSITO — reloj crédito día 55
        exp2 = make_exp("SONDEL-CR", "FULL", "TRANSITO", 60,
                        credit_clock_started_at=now - timedelta(days=55))
        make_artifact(exp2, "ART-01", {"po_number": "PO-504855", "total": 28750.00}, 60)
        make_artifact(exp2, "ART-05", {"carrier": "Copa Cargo", "awb": "230-87654321"}, 55)
        make_cost(exp2, "merchandise", 28750.00, "PRODUCCION", 55)
        make_cost(exp2, "freight_air", 3200.00, "DESPACHO", 50)
        make_event(exp2, "expediente.created", 60)

        # 3. EN_DESTINO — UMMIE, reloj día 78 ⚠️
        exp3 = make_exp("UMMIE-GT", "COMISION", "EN_DESTINO", 85,
                        credit_clock_started_at=now - timedelta(days=78),
                        payment_status="partial")
        make_artifact(exp3, "ART-01", {"po_number": "PO-GT-2026-001", "total": 15200.00}, 85)
        make_artifact(exp3, "ART-05", {"carrier": "DHL Express", "awb": "1234567890"}, 78)
        make_cost(exp3, "merchandise", 15200.00, "PRODUCCION", 80)
        make_cost(exp3, "freight_air", 1890.00, "DESPACHO", 75)
        make_payment(exp3, 800.00, "wire", "UMMIE-PARTIAL-001", 30)
        make_event(exp3, "expediente.created", 85)
        make_event(exp3, "credit_clock.warning", 18)

        # 4. BLOQUEADO — reloj día 82 🔴
        exp4 = make_exp("SONDEL-CR", "FULL", "TRANSITO", 88,
                        is_blocked=True,
                        blocked_reason="Credit clock >75 days — auto block",
                        blocked_at=now - timedelta(days=7),
                        blocked_by_type="SYSTEM",
                        credit_clock_started_at=now - timedelta(days=82))
        make_artifact(exp4, "ART-01", {"po_number": "PO-504900", "total": 42100.00}, 88)
        make_artifact(exp4, "ART-05", {"carrier": "Copa Cargo", "awb": "230-11112222"}, 82)
        make_cost(exp4, "merchandise", 42100.00, "PRODUCCION", 85)
        make_event(exp4, "expediente.blocked", 7, {"reason": "Credit clock >75 days"})

        # 5. REGISTRO — recién creado
        exp5 = make_exp("IMPORCOMP-CO", "COMISION", "REGISTRO", 3)
        make_artifact(exp5, "ART-01", {"po_number": "PO-CO-2026-015", "total": 8500.00}, 3)
        make_event(exp5, "expediente.created", 3)

        # 6. PRODUCCION
        exp6 = make_exp("SONDEL-CR", "FULL", "PRODUCCION", 30)
        make_artifact(exp6, "ART-01", {"po_number": "PO-505100", "total": 22300.00}, 30)
        make_cost(exp6, "merchandise", 22300.00, "PRODUCCION", 25)
        make_event(exp6, "expediente.created", 30)

        # 7. PREPARACION
        exp7 = make_exp("UMMIE-GT", "COMISION", "PREPARACION", 45)
        make_artifact(exp7, "ART-01", {"po_number": "PO-GT-2026-002", "total": 11800.00}, 45)
        make_cost(exp7, "merchandise", 11800.00, "PRODUCCION", 40)
        make_event(exp7, "expediente.created", 45)

        # 8. DESPACHO
        exp8 = make_exp("SONDEL-CR", "FULL", "DESPACHO", 50,
                        credit_clock_started_at=now - timedelta(days=15))
        make_artifact(exp8, "ART-01", {"po_number": "PO-505200", "total": 19500.00}, 50)
        make_artifact(exp8, "ART-05", {"carrier": "Copa Cargo", "awb": "230-33334444"}, 15)
        make_cost(exp8, "merchandise", 19500.00, "PRODUCCION", 45)
        make_cost(exp8, "freight_air", 2800.00, "DESPACHO", 15)
        make_event(exp8, "expediente.created", 50)

        # 9. CANCELADO
        exp9 = make_exp("IMPORCOMP-CO", "COMISION", "CANCELADO", 40)
        make_artifact(exp9, "ART-01", {"po_number": "PO-CO-2026-010", "total": 5200.00}, 40)
        make_event(exp9, "expediente.cancelled", 35, {"reason": "Cliente canceló PO"})

        # 10. CERRADO modelo B
        exp10 = make_exp("UMMIE-GT", "COMISION", "CERRADO", 120,
                         payment_status="paid",
                         credit_clock_started_at=now - timedelta(days=100))
        make_artifact(exp10, "ART-01", {"po_number": "PO-GT-2025-050", "total": 9800.00}, 120)
        make_artifact(exp10, "ART-05", {"carrier": "DHL", "awb": "5556667778"}, 100)
        make_cost(exp10, "merchandise", 9800.00, "PRODUCCION", 115)
        make_cost(exp10, "freight_air", 1200.00, "DESPACHO", 98)
        make_payment(exp10, 918.26, "liquidacion_marluvas", "LIQ-2025-12", 20)
        make_event(exp10, "expediente.completed", 15)

        self.stdout.write(self.style.SUCCESS("\n✅ 10 expedientes creados"))

        # ── NODOS + TRANSFERS ──────────────────────────────────────────
        if HAS_TRANSFERS:
            self.stdout.write("\nCreando nodos y transfers...")
            try:
                node_fiscal, _ = Node.objects.get_or_create(
                    node_id="DEMO-FISCAL-CR",
                    defaults={"name": "Almacén Fiscal CR", "node_type": "fiscal", "status": "active"})
                node_own, _ = Node.objects.get_or_create(
                    node_id="DEMO-OWN-WH-CR",
                    defaults={"name": "Bodega MWT CR", "node_type": "owned_warehouse", "status": "active"})
                node_fba, _ = Node.objects.get_or_create(
                    node_id="DEMO-FBA-US",
                    defaults={"name": "Amazon FBA USA", "node_type": "fba", "status": "active"})

                trf1 = Transfer.objects.create(
                    transfer_id="TRF-DEMO-001", from_node=node_fiscal, to_node=node_own,
                    ownership_changes=False, legal_context="nationalization",
                    customs_required=True, status="in_transit", source_expediente=exp1)
                TransferLine.objects.create(transfer=trf1, sku="RW-GOL-MED-S3", quantity_dispatched=200)
                TransferLine.objects.create(transfer=trf1, sku="RW-GOL-MED-S4", quantity_dispatched=300)

                trf2 = Transfer.objects.create(
                    transfer_id="TRF-DEMO-002", from_node=node_own, to_node=node_fba,
                    ownership_changes=False, legal_context="internal",
                    customs_required=False, status="planned")
                TransferLine.objects.create(transfer=trf2, sku="RW-GOL-MED-S3", quantity_dispatched=100)

                self.stdout.write(self.style.SUCCESS("  2 transfers + 3 nodos creados"))
            except Exception as e:
                self.stderr.write(f"  WARN transfers: {e}")

        # ── LIQUIDACIÓN ────────────────────────────────────────────────
        if HAS_LIQUIDATIONS:
            self.stdout.write("\nCreando liquidación demo...")
            try:
                liq = Liquidation.objects.create(
                    period="DEMO-2026-02", brand="marluvas", status="in_review")
                LiquidationLine.objects.create(
                    liquidation=liq, marluvas_reference="2354-2025", concept="comision",
                    client_payment_amount=Decimal("9800.00"),
                    commission_pct_reported=Decimal("9.37"),
                    commission_amount=Decimal("918.26"), currency="USD",
                    match_status="matched", matched_expediente=exp10)
                LiquidationLine.objects.create(
                    liquidation=liq, marluvas_reference="PREMIO-FEB", concept="premio",
                    client_payment_amount=Decimal("0"),
                    commission_pct_reported=Decimal("0"),
                    commission_amount=Decimal("1201.80"), currency="USD",
                    match_status="no_match_needed")
                self.stdout.write(self.style.SUCCESS("  1 liquidación + 2 líneas creadas"))
            except Exception as e:
                self.stderr.write(f"  WARN liquidation: {e}")

        self.stdout.write(self.style.SUCCESS("""
✅ SEED COMPLETADO
  EXP-001  CERRADO      Sondel CR     FULL     Happy path
  EXP-002  TRANSITO     Sondel CR     FULL     Reloj día 55
  EXP-003  EN_DESTINO   UMMIE GT      COMISION Reloj día 78 ⚠️
  EXP-004  TRANSITO     Sondel CR     FULL     Bloqueado día 82 🔴
  EXP-005  REGISTRO     Imporcomp CO  COMISION Recién creado
  EXP-006  PRODUCCION   Sondel CR     FULL     En fábrica
  EXP-007  PREPARACION  UMMIE GT      COMISION Listo despachar
  EXP-008  DESPACHO     Sondel CR     FULL     Embarcando
  EXP-009  CANCELADO    Imporcomp CO  COMISION PO cancelada
  EXP-010  CERRADO      UMMIE GT      COMISION Modelo B pagado

  Para limpiar: python manage.py seed_demo_data --flush
"""))
