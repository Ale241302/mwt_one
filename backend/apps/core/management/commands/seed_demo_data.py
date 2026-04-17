"""seed_demo_data.py — Management command para poblar mwt.one con datos de demo

Uso:   python manage.py seed_demo_data
Limpia: python manage.py seed_demo_data --flush
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid


class Command(BaseCommand):
    help = "Seed demo data for mwt.one"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete all demo data first")

    def handle(self, *args, **options):
        from apps.expedientes.models import (
            Expediente, ArtifactInstance, CostLine, PaymentLine, EventLog
        )
        from apps.transfers.models import Transfer, TransferLine
        from apps.nodos.models import Node
        from apps.core.models import LegalEntity

        try:
            from apps.liquidations.models import Liquidation, LiquidationLine
            HAS_LIQUIDATIONS = True
        except ImportError:
            HAS_LIQUIDATIONS = False
            self.stdout.write("WARN: Liquidations module not found — skipping")

        # ── FLUSH ──────────────────────────────────────────────────────────────
        if options["flush"]:
            self.stdout.write("Flushing demo data...")
            demo_exps = Expediente.objects.filter(
                client__entity_id__in=["CLIENT_A-CR", "CLIENT_B-GT", "CLIENT_C-CO"],
                brand__isnull=True,
            )
            demo_exp_ids = list(demo_exps.values_list('pk', flat=True))
            EventLog.objects.filter(aggregate_id__in=demo_exp_ids).delete()
            PaymentLine.objects.filter(expediente__in=demo_exps).delete()
            CostLine.objects.filter(expediente__in=demo_exps).delete()
            ArtifactInstance.objects.filter(expediente__in=demo_exps).delete()
            demo_exps.delete()
            Transfer.objects.filter(transfer_id__startswith="TRF-DEMO").delete()
            Node.objects.filter(name__startswith="DEMO ").delete()
            LegalEntity.objects.filter(entity_id__in=["CLIENT_A-CR", "CLIENT_B-GT", "CLIENT_C-CO", "MWT-CR"]).delete()
            if HAS_LIQUIDATIONS:
                Liquidation.objects.filter(period__startswith="DEMO-").delete()
            self.stdout.write(self.style.SUCCESS("Flushed."))
            return

        now = timezone.now()
        self.stdout.write("Seeding demo data...")

        # ── LEGAL ENTITIES ─────────────────────────────────────────────────────
        mwt_cr, _ = LegalEntity.objects.get_or_create(
            entity_id="MWT-CR",
            defaults=dict(legal_name="MWT Costa Rica S.A.", country="CRI",
                          role="OWNER", relationship_to_mwt="SELF",
                          frontend="MWT_ONE", visibility_level="FULL",
                          pricing_visibility="INTERNAL", status="ACTIVE")
        )
        sondel_cr, _ = LegalEntity.objects.get_or_create(
            entity_id="CLIENT_A-CR",
            defaults=dict(legal_name="Client_A Costa Rica S.A.", country="CRI",
                          role="DISTRIBUTOR", relationship_to_mwt="DISTRIBUTION",
                          frontend="MWT_ONE", visibility_level="FULL",
                          pricing_visibility="CLIENT", status="ACTIVE")
        )
        ummie_gt, _ = LegalEntity.objects.get_or_create(
            entity_id="CLIENT_B-GT",
            defaults=dict(legal_name="CLIENT_B Guatemala S.A.", country="GTM",
                          role="DISTRIBUTOR", relationship_to_mwt="DISTRIBUTION",
                          frontend="MWT_ONE", visibility_level="FULL",
                          pricing_visibility="CLIENT", status="ACTIVE")
        )
        imporcomp_co, _ = LegalEntity.objects.get_or_create(
            entity_id="CLIENT_C-CO",
            defaults=dict(legal_name="Client_C Colombia S.A.S.", country="COL",
                          role="DISTRIBUTOR", relationship_to_mwt="DISTRIBUTION",
                          frontend="MWT_ONE", visibility_level="FULL",
                          pricing_visibility="CLIENT", status="ACTIVE")
        )

        # ── HELPERS ────────────────────────────────────────────────────────────
        def make_exp(client_entity, mode, status, days_ago, **kwargs):
            exp = Expediente.objects.create(
                brand=None,  # nullable FK — no brand assigned for demo
                legal_entity=mwt_cr,
                client=client_entity,
                mode=mode,
                status=status,
                freight_mode=kwargs.get("freight_mode", "prepaid"),
                transport_mode=kwargs.get("transport_mode", "aereo"),
                dispatch_mode=kwargs.get("dispatch_mode", "MWT"),
                is_blocked=kwargs.get("is_blocked", False),
                blocked_reason=kwargs.get("blocked_reason", None),
                blocked_at=kwargs.get("blocked_at", None),
                blocked_by_type=kwargs.get("blocked_by_type", None),
                payment_status=kwargs.get("payment_status", "PENDING"),
                credit_clock_started_at=kwargs.get("credit_clock_started_at", None),
            )
            Expediente.objects.filter(pk=exp.pk).update(
                created_at=now - timedelta(days=days_ago)
            )
            exp.refresh_from_db()
            self.stdout.write(f"  EXP {str(exp.pk)[:8]} [{status}] — {client_entity.entity_id} ({mode})")
            return exp

        def make_artifact(exp, art_type, status="COMPLETED", payload=None, days_ago=0):
            art = ArtifactInstance.objects.create(
                expediente=exp, artifact_type=art_type,
                status=status, payload=payload or {},
            )
            if days_ago:
                ArtifactInstance.objects.filter(pk=art.pk).update(
                    created_at=now - timedelta(days=days_ago)
                )
            return art

        def make_cost(exp, concept, amount, phase, days_ago=0):
            cl = CostLine.objects.create(
                expediente=exp, cost_type=concept,
                amount=Decimal(str(amount)), currency="USD",
                phase=phase, description=f"{concept} — demo",
                visibility="INTERNAL",
            )
            if days_ago:
                CostLine.objects.filter(pk=cl.pk).update(
                    created_at=now - timedelta(days=days_ago)
                )
            return cl

        def make_payment(exp, amount, method="wire", reference="", days_ago=0):
            return PaymentLine.objects.create(
                expediente=exp,
                amount=Decimal(str(amount)), currency="USD",
                method=method, reference=reference,
                registered_at=now - timedelta(days=days_ago),
                registered_by_type="CEO",
                registered_by_id="seed_demo_data",
            )

        def make_event(exp, event_type, days_ago=0, data=None):
            EventLog.objects.create(
                event_type=event_type,
                aggregate_type="EXPEDIENTE",
                aggregate_id=exp.pk,
                payload=data or {},
                occurred_at=now - timedelta(days=days_ago),
                emitted_by="seed_demo_data",
                correlation_id=uuid.uuid4(),
            )

        # ── EXPEDIENTES ────────────────────────────────────────────────────────
        exp1 = make_exp(sondel_cr, "FULL", "CERRADO", 90,
                        payment_status="PAID",
                        credit_clock_started_at=now - timedelta(days=85))
        make_artifact(exp1, "ART-01", payload={"po_number": "PO-504652", "total": 33542.00}, days_ago=90)
        make_artifact(exp1, "ART-02", payload={"consecutive": "2395-2025", "total_usd": 33542.00}, days_ago=88)
        make_artifact(exp1, "ART-05", payload={"carrier": "Copa Cargo", "awb": "230-12345678", "route": "CNF→PTY→SJO"}, days_ago=60)
        make_artifact(exp1, "ART-09", payload={"invoice_number": "FE-001-0001234", "total": 47693.00}, days_ago=10)
        make_cost(exp1, "merchandise", 33542.00, "PRODUCCION", 85)
        make_cost(exp1, "freight_air", 4850.00, "DESPACHO", 58)
        make_cost(exp1, "customs_dai", 4695.88, "EN_DESTINO", 25)
        make_cost(exp1, "customs_iva", 5583.34, "EN_DESTINO", 25)
        make_payment(exp1, 47693.00, "wire", "TRF-CLIENT_A-2025-12", 8)
        make_event(exp1, "expediente.created", 90)
        make_event(exp1, "expediente.state_changed", 85, {"from": "REGISTRO", "to": "PRODUCCION"})
        make_event(exp1, "expediente.state_changed", 58, {"from": "PREPARACION", "to": "DESPACHO"})
        make_event(exp1, "expediente.state_changed", 25, {"from": "TRANSITO", "to": "EN_DESTINO"})
        make_event(exp1, "expediente.completed", 8)

        exp2 = make_exp(sondel_cr, "FULL", "TRANSITO", 60,
                        credit_clock_started_at=now - timedelta(days=55))
        make_artifact(exp2, "ART-01", payload={"po_number": "PO-504855", "total": 28750.00}, days_ago=60)
        make_artifact(exp2, "ART-05", payload={"carrier": "Copa Cargo", "awb": "230-87654321"}, days_ago=55)
        make_cost(exp2, "merchandise", 28750.00, "PRODUCCION", 55)
        make_cost(exp2, "freight_air", 3200.00, "DESPACHO", 50)
        make_event(exp2, "expediente.created", 60)
        make_event(exp2, "expediente.state_changed", 48, {"from": "DESPACHO", "to": "TRANSITO"})

        exp3 = make_exp(ummie_gt, "COMISION", "EN_DESTINO", 85,
                        credit_clock_started_at=now - timedelta(days=78),
                        payment_status="PARTIAL")
        make_artifact(exp3, "ART-01", payload={"po_number": "PO-GT-2026-001", "total": 15200.00}, days_ago=85)
        make_artifact(exp3, "ART-05", payload={"carrier": "DHL Express", "awb": "1234567890"}, days_ago=78)
        make_cost(exp3, "merchandise", 15200.00, "PRODUCCION", 80)
        make_payment(exp3, 800.00, "wire", "CLIENT_B-PARTIAL-001", 30)
        make_event(exp3, "expediente.created", 85)
        make_event(exp3, "credit_clock.warning", 18)

        exp4 = make_exp(sondel_cr, "FULL", "TRANSITO", 88,
                        is_blocked=True,
                        blocked_reason="Credit clock >75 days — auto block",
                        blocked_at=now - timedelta(days=7),
                        blocked_by_type="SYSTEM",
                        credit_clock_started_at=now - timedelta(days=82))
        make_artifact(exp4, "ART-01", payload={"po_number": "PO-504900", "total": 42100.00}, days_ago=88)
        make_cost(exp4, "merchandise", 42100.00, "PRODUCCION", 85)
        make_event(exp4, "expediente.blocked", 7, {"reason": "Credit clock >75 days"})

        exp5 = make_exp(imporcomp_co, "COMISION", "REGISTRO", 3)
        make_artifact(exp5, "ART-01", payload={"po_number": "PO-CO-2026-015", "total": 8500.00}, days_ago=3)
        make_event(exp5, "expediente.created", 3)

        exp6 = make_exp(sondel_cr, "FULL", "PRODUCCION", 30)
        make_artifact(exp6, "ART-01", payload={"po_number": "PO-505100", "total": 22300.00}, days_ago=30)
        make_cost(exp6, "merchandise", 22300.00, "PRODUCCION", 25)
        make_event(exp6, "expediente.created", 30)

        exp7 = make_exp(ummie_gt, "COMISION", "PREPARACION", 45)
        make_artifact(exp7, "ART-01", payload={"po_number": "PO-GT-2026-002", "total": 11800.00}, days_ago=45)
        make_cost(exp7, "merchandise", 11800.00, "PRODUCCION", 40)
        make_event(exp7, "expediente.created", 45)

        exp8 = make_exp(sondel_cr, "FULL", "DESPACHO", 50,
                        credit_clock_started_at=now - timedelta(days=15))
        make_artifact(exp8, "ART-01", payload={"po_number": "PO-505200", "total": 19500.00}, days_ago=50)
        make_artifact(exp8, "ART-05", payload={"carrier": "Copa Cargo", "awb": "230-33334444"}, days_ago=15)
        make_cost(exp8, "merchandise", 19500.00, "PRODUCCION", 45)
        make_cost(exp8, "freight_air", 2800.00, "DESPACHO", 15)
        make_event(exp8, "expediente.created", 50)
        make_event(exp8, "expediente.state_changed", 15, {"from": "PREPARACION", "to": "DESPACHO"})

        exp9 = make_exp(imporcomp_co, "COMISION", "CANCELADO", 40)
        make_artifact(exp9, "ART-01", payload={"po_number": "PO-CO-2026-010", "total": 5200.00}, days_ago=40)
        make_event(exp9, "expediente.created", 40)
        make_event(exp9, "expediente.cancelled", 35, {"reason": "Cliente canceló PO"})

        exp10 = make_exp(ummie_gt, "COMISION", "CERRADO", 120,
                         payment_status="PAID",
                         credit_clock_started_at=now - timedelta(days=100))
        make_artifact(exp10, "ART-01", payload={"po_number": "PO-GT-2025-050", "total": 9800.00}, days_ago=120)
        make_artifact(exp10, "ART-05", payload={"carrier": "DHL", "awb": "5556667778"}, days_ago=100)
        make_cost(exp10, "merchandise", 9800.00, "PRODUCCION", 115)
        make_cost(exp10, "freight_air", 1200.00, "DESPACHO", 98)
        make_payment(exp10, 918.26, "liquidacion_marluvas", "LIQ-2025-12", 20)
        make_event(exp10, "expediente.created", 120)
        make_event(exp10, "expediente.completed", 15)

        self.stdout.write(self.style.SUCCESS("\n✅ 10 expedientes creados"))

        # ── NODOS + TRANSFERS ──────────────────────────────────────────────────
        self.stdout.write("\nCreando nodos y transfers...")
        try:
            node_fiscal, _ = Node.objects.get_or_create(
                name="DEMO Almacén Fiscal CR",
                defaults={"node_type": "fiscal", "status": "active", "legal_entity": mwt_cr})
            node_own, _ = Node.objects.get_or_create(
                name="DEMO Bodega MWT CR",
                defaults={"node_type": "logistics_hub", "status": "active", "legal_entity": mwt_cr})
            node_fba, _ = Node.objects.get_or_create(
                name="DEMO Amazon FBA USA",
                defaults={"node_type": "destination", "status": "active", "legal_entity": mwt_cr})

            trf1 = Transfer.objects.create(
                transfer_id="TRF-DEMO-001",
                from_node=node_fiscal, to_node=node_own,
                ownership_before=mwt_cr, ownership_after=mwt_cr,
                ownership_changes=False, legal_context="nationalization",
                customs_required=True, status="in_transit",
                source_expediente=exp1,
            )
            TransferLine.objects.create(transfer=trf1, sku="RW-GOL-MED-S3", quantity_dispatched=200)
            TransferLine.objects.create(transfer=trf1, sku="RW-GOL-MED-S4", quantity_dispatched=300)

            trf2 = Transfer.objects.create(
                transfer_id="TRF-DEMO-002",
                from_node=node_own, to_node=node_fba,
                ownership_before=mwt_cr, ownership_after=mwt_cr,
                ownership_changes=False, legal_context="internal",
                customs_required=False, status="planned",
            )
            TransferLine.objects.create(transfer=trf2, sku="RW-GOL-MED-S3", quantity_dispatched=100)
            TransferLine.objects.create(transfer=trf2, sku="RW-GOL-MED-S4", quantity_dispatched=150)

            self.stdout.write(self.style.SUCCESS("  2 transfers + 3 nodos creados"))
        except Exception as e:
            self.stderr.write(f"  WARN transfers: {e}")

        # ── LIQUIDACIÓN ────────────────────────────────────────────────────────
        if HAS_LIQUIDATIONS:
            self.stdout.write("\nCreando liquidación demo...")
            try:
                liq = Liquidation.objects.create(
                    period="DEMO-2026-02", brand="marluvas", status="in_review")
                LiquidationLine.objects.create(
                    liquidation=liq, marluvas_reference="2354-2025",
                    concept="comision", client_payment_amount=Decimal("9800.00"),
                    commission_pct_reported=Decimal("9.37"),
                    commission_amount=Decimal("918.26"), currency="USD",
                    match_status="matched", matched_expediente=exp10)
                LiquidationLine.objects.create(
                    liquidation=liq, marluvas_reference="2428-2026",
                    concept="comision", client_payment_amount=Decimal("7600.00"),
                    commission_pct_reported=Decimal("10.00"),
                    commission_amount=Decimal("760.00"), currency="USD",
                    match_status="matched", matched_expediente=exp3,
                    is_partial_payment=True)
                LiquidationLine.objects.create(
                    liquidation=liq, marluvas_reference="PREMIO-FEB",
                    concept="premio", client_payment_amount=Decimal("0"),
                    commission_pct_reported=Decimal("0"),
                    commission_amount=Decimal("1201.80"), currency="USD",
                    match_status="no_match_needed")
                self.stdout.write(self.style.SUCCESS("  1 liquidación + 3 líneas creadas"))
            except Exception as e:
                self.stderr.write(f"  WARN liquidation: {e}")

        self.stdout.write(self.style.SUCCESS("""
╔══════════════════════════════════════════════════════════════════╗
║                    SEED DATA COMPLETADO                         ║
╠══════════════════════════════════════════════════════════════════╣
║  EXP-001  CERRADO      Client_A CR    FULL     Happy path        ║
║  EXP-002  TRANSITO     Client_A CR    FULL     Reloj día 55      ║
║  EXP-003  EN_DESTINO   CLIENT_B GT     COMISION Reloj día 78 ⚠   ║
║  EXP-004  BLOQUEADO    Client_A CR    FULL     Reloj día 82 🔴   ║
║  EXP-005  REGISTRO     Client_C CO COMISION Recién creado     ║
║  EXP-006  PRODUCCION   Client_A CR    FULL     En fábrica        ║
║  EXP-007  PREPARACION  CLIENT_B GT     COMISION Listo despachar   ║
║  EXP-008  DESPACHO     Client_A CR    FULL     Embarcando        ║
║  EXP-009  CANCELADO    Client_C CO COMISION PO cancelada      ║
║  EXP-010  CERRADO      CLIENT_B GT     COMISION Modelo B pagado   ║
║                                                                 ║
║  Para limpiar: python manage.py seed_demo_data --flush          ║
╚══════════════════════════════════════════════════════════════════╝
"""))
