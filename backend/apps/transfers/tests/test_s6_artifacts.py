from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.transfers.models import Transfer, Node
from apps.transfers.enums import TransferStatus
from apps.expedientes.models import Expediente, ArtifactInstance
from apps.brands.models import Brand
from apps.expedientes.enums import ExpedienteStatus, BrandType
from apps.transfers.services import (
    create_pricing_approval_artifact,
    approve_transfer,
    create_preparation_artifact
)

User = get_user_model()

class TransferArtifactTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ceo", is_staff=True, is_superuser=True)
        self.brand = Brand.objects.create(name="Rana Walk", slug="rana_walk", brand_type=BrandType.RANA_WALK)
        
        self.node_a = Node.objects.create(name="Node A", region="US")
        self.node_b = Node.objects.create(name="Node B", region="CR")
        
        self.expediente = Expediente.objects.create(
            unique_id="EXP-123",
            status=ExpedienteStatus.DRAFT,
            brand=self.brand
        )
        
        self.transfer = Transfer.objects.create(
            transfer_id="TR-1",
            source_expediente=self.expediente,
            source_node=self.node_a,
            destination_node=self.node_b,
            status=TransferStatus.PLANNED,
            ownership_changes=True,
            created_by=self.user
        )

    def test_approve_transfer_fails_without_art16(self):
        # Should fail since ownership_changes=True but no ART-16 exists
        with self.assertRaises(ValueError):
            approve_transfer(self.transfer, self.user)

    def test_approve_transfer_succeeds_with_art16(self):
        # Create ART-16
        create_pricing_approval_artifact(self.transfer, {"price": 100}, self.user)
        
        # Now it should succeed
        approved_transfer = approve_transfer(self.transfer, self.user)
        self.assertEqual(approved_transfer.status, TransferStatus.APPROVED)

    def test_create_preparation_artifact_validates_status(self):
        # Cannot prepare if not approved
        with self.assertRaises(ValueError):
            create_preparation_artifact(self.transfer, {"packing": "box"}, self.user)
            
        # Approve it first (with ART-16, since ownership changes)
        create_pricing_approval_artifact(self.transfer, {}, self.user)
        approve_transfer(self.transfer, self.user)
        
        # Now prepare should work
        art14 = create_preparation_artifact(self.transfer, {"packing": "box"}, self.user)
        self.assertEqual(art14.artifact_type, "ART-14")
        self.transfer.refresh_from_db()
        self.assertEqual(self.transfer.status, TransferStatus.PREPARED)
