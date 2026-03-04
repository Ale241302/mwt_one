import pytest
from unittest.mock import patch
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.liquidations.models import Liquidation, LiquidationLine
from apps.liquidations.enums import LiquidationStatus, MatchStatus, LiquidationLineConcept
from apps.expedientes.models import Expediente, LegalEntity, ArtifactInstance
from apps.expedientes.enums import ExpedienteStatus

User = get_user_model()

@pytest.mark.django_db
class TestLiquidationCommands:
    def setup_method(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="admin@admin.com", email="admin@admin.com", password="pwd", is_staff=True, is_superuser=True
        )
        self.client.force_authenticate(user=self.admin_user)
        
        # Setup Legal Entity
        from apps.expedientes.enums import LegalEntityRole, LegalEntityRelationship, LegalEntityFrontend, LegalEntityVisibility, PricingVisibility
        self.le = LegalEntity.objects.create(
            entity_id="LE_MARLUVAS", legal_name="Marluvas", country="BR", role=LegalEntityRole.DISTRIBUTOR, 
            relationship_to_mwt=LegalEntityRelationship.DISTRIBUTION, frontend=LegalEntityFrontend.EXTERNAL, 
            visibility_level=LegalEntityVisibility.FULL, pricing_visibility=PricingVisibility.CLIENT
        )
        
        # Setup Expediente with ART-02
        self.expediente = Expediente.objects.create(
            status=ExpedienteStatus.PREPARACION,
            legal_entity=self.le,
            client=self.le
        )
        
        # Create an ART-02 artifact representing a proforma
        self.proforma = ArtifactInstance.objects.create(
            expediente=self.expediente,
            artifact_type="ART-02",
            status="completed",
            payload={
                "consecutive": "PROF-12345",
                "total_amount": 1000.00,
                "comision_pactada": 10.00
            }
        )

    @patch('apps.liquidations.services.parse_marluvas_excel')
    def test_c25_upload_liquidation(self, mock_parse):
        # We need to mock the parser since Phase B isn't active
        from decimal import Decimal
        mock_parse.return_value = (
            [
                {
                    "concept": LiquidationLineConcept.COMISION,
                    "marluvas_reference": "PROF-12345",
                    "client_payment_amount": Decimal("1000.00"),
                    "commission_amount": Decimal("100.00"),
                    "commission_pct_reported": Decimal("10.00")
                },
                {
                    "concept": LiquidationLineConcept.PREMIO,
                    "marluvas_reference": "PREMIO-01",
                    "client_payment_amount": Decimal("0.00"),
                    "commission_amount": Decimal("50.00"),
                    "commission_pct_reported": Decimal("0.00")
                }
            ],
            "" # No error
        )
        
        test_file = SimpleUploadedFile("test_liq.xlsx", b"file_content", content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        payload = {
            "file": test_file,
            "period": "2023-10"
        }
        
        res = self.client.post("/api/liquidations/upload/", payload, format='multipart')
        assert res.status_code == status.HTTP_201_CREATED
        
        data = res.json()
        assert data["period"] == "2023-10"
        assert data["status"] == LiquidationStatus.PENDING
        
        liq = Liquidation.objects.get(liquidation_id=data["liquidation_id"])
        assert liq.total_lines == 2
        
        # Check auto-match logic
        lines = liq.lines.all().order_by('concept')
        comision_line = lines.get(concept=LiquidationLineConcept.COMISION)
        premio_line = lines.get(concept=LiquidationLineConcept.PREMIO)
        
        assert comision_line.match_status == MatchStatus.MATCHED
        assert comision_line.matched_proforma == self.proforma
        
        assert premio_line.match_status == MatchStatus.NO_MATCH_NEEDED

    def test_c26_manual_match_line(self):
        # Create un-matched liquidation line
        liq = Liquidation.objects.create(period="2023-11", status=LiquidationStatus.PENDING)
        line = LiquidationLine.objects.create(
            liquidation=liq, marluvas_reference="MISSING", concept=LiquidationLineConcept.COMISION,
            client_payment_amount=1000.00, commission_pct_reported=10.00, commission_amount=100.00,
            match_status=MatchStatus.UNMATCHED
        )
        
        # Make another proforma to map to
        proforma2 = ArtifactInstance.objects.create(
            expediente=self.expediente, artifact_type="ART-02", status="completed",
            payload={"consecutive": "PROF-999", "total_amount": 1000.00, "comision_pactada": 10.00}
        )
        
        payload = {"line_id": line.id, "proforma_id": str(proforma2.artifact_id)}
        res = self.client.post(f"/api/liquidations/{liq.liquidation_id}/match-line/", payload, format='json')
        assert res.status_code == status.HTTP_200_OK
        
        line.refresh_from_db()
        assert line.match_status == MatchStatus.MATCHED
        assert line.matched_proforma == proforma2
        
    def test_c27_reconcile_liquidation(self):
        liq = Liquidation.objects.create(period="2023-12", status=LiquidationStatus.PENDING)
        
        # Valid lines
        LiquidationLine.objects.create(
            liquidation=liq, marluvas_reference="MATCHED", concept=LiquidationLineConcept.COMISION,
            client_payment_amount=1000.00, commission_pct_reported=10.00, commission_amount=100.00,
            match_status=MatchStatus.MATCHED, matched_proforma=self.proforma
        )
        LiquidationLine.objects.create(
            liquidation=liq, marluvas_reference="PREMIO", concept=LiquidationLineConcept.PREMIO,
            client_payment_amount=0.00, commission_pct_reported=0.00, commission_amount=50.00,
            match_status=MatchStatus.NO_MATCH_NEEDED
        )
        
        res = self.client.post(f"/api/liquidations/{liq.liquidation_id}/reconcile/")
        assert res.status_code == status.HTTP_200_OK
        
        liq.refresh_from_db()
        assert liq.status == LiquidationStatus.RECONCILED
        assert liq.total_commission_amount == 150.00
        
    def test_c27_reconcile_liquidation_blocking_lines(self):
        liq = Liquidation.objects.create(period="2023-13", status=LiquidationStatus.PENDING)
        
        # Invalid Line
        LiquidationLine.objects.create(
            liquidation=liq, marluvas_reference="DISCREPANCY", concept=LiquidationLineConcept.COMISION,
            client_payment_amount=500.00, commission_pct_reported=10.00, commission_amount=50.00,
            match_status=MatchStatus.DISCREPANCY, matched_proforma=self.proforma
        )
        
        try:
            res = self.client.post(f"/api/liquidations/{liq.liquidation_id}/reconcile/")
            assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        except ValueError as e:
            assert "Resolve all lines before reconciling" in str(e)
            
    def test_c28_dispute_liquidation(self):
        liq = Liquidation.objects.create(period="2023-14", status=LiquidationStatus.PENDING)
        
        payload = {"observations": "Payment amounts missing."}
        res = self.client.post(f"/api/liquidations/{liq.liquidation_id}/dispute/", payload, format='json')
        
        assert res.status_code == status.HTTP_200_OK
        
        liq.refresh_from_db()
        assert liq.status == LiquidationStatus.DISPUTED
        assert liq.observations == "Payment amounts missing."
