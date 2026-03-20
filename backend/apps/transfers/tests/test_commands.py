import pytest
from rest_framework import status
from rest_framework.test import APIClient
from apps.transfers.models import Transfer, TransferLine, Node
from apps.transfers.enums_exp import NodeStatus, NodeType, LegalContext, TransferStatus
from django.contrib.auth import get_user_model
User = get_user_model()
from apps.expedientes.models import LegalEntity

@pytest.mark.django_db
class TestTransferCommands:
    def setup_method(self):
        self.client = APIClient()

        # Users
        self.admin_user = User.objects.create_user(
            username="admin@admin.com", email="admin@admin.com", password="pwd", is_staff=True, is_superuser=True
        )
        self.ops_user = User.objects.create_user(
            username="ops@test.com", email="ops@test.com", password="pwd"
        )
        
        # Legal Entities
        from apps.expedientes.enums_exp import LegalEntityRole, LegalEntityRelationship, LegalEntityFrontend, LegalEntityVisibility, PricingVisibility
        
        self.le_from = LegalEntity.objects.create(
            entity_id="SENDER1", legal_name="Sender LE", country="AR", role=LegalEntityRole.OWNER, 
            relationship_to_mwt=LegalEntityRelationship.SELF, frontend=LegalEntityFrontend.EXTERNAL, 
            visibility_level=LegalEntityVisibility.FULL, pricing_visibility=PricingVisibility.CLIENT
        )
        self.le_to = LegalEntity.objects.create(
            entity_id="RECEIVER1", legal_name="Receiver LE", country="BR", role=LegalEntityRole.DISTRIBUTOR, 
            relationship_to_mwt=LegalEntityRelationship.DISTRIBUTION, frontend=LegalEntityFrontend.EXTERNAL, 
            visibility_level=LegalEntityVisibility.FULL, pricing_visibility=PricingVisibility.CLIENT
        )

        # Nodes
        self.node_from = Node.objects.create(
            name="Origin Node", legal_entity=self.le_from, node_type=NodeType.OWNED_WAREHOUSE
        )
        self.node_to = Node.objects.create(
            name="Dest Node", legal_entity=self.le_to, node_type=NodeType.THIRD_PARTY
        )
        
    def test_c30_create_transfer(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "from_node": str(self.node_from.node_id),
            "to_node": str(self.node_to.node_id),
            "legal_context": LegalContext.INTERNAL,
            "items": [
                {"sku": "SKU1", "quantity": 10},
                {"sku": "SKU2", "quantity": 5},
            ]
        }
        res = self.client.post("/api/transfers/create/", payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED, res.data
        
        data = res.json()
        assert data["status"] == TransferStatus.PLANNED
        assert len(data["lines"]) == 2
        
        trf = Transfer.objects.get(transfer_id=data["transfer_id"])
        # Validate node details populated correctly
        assert trf.from_node == self.node_from
        assert trf.legal_context == LegalContext.INTERNAL
        assert trf.ownership_changes is True  # Because from_le != to_le
        
    def test_c30_create_transfer_same_node_error(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "from_node": str(self.node_from.node_id),
            "to_node": str(self.node_from.node_id), # Same node
            "legal_context": LegalContext.INTERNAL,
            "items": [{"sku": "SKU1", "quantity": 10}]
        }
        
        from django.core.exceptions import ValidationError
        try:
            res = self.client.post("/api/transfers/create/", payload, format='json')
            assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        except ValidationError as e:
            assert "from_node and to_node must be different" in str(e)

    def test_transfer_lifecycle(self):
        # 1. CREATE
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "from_node": str(self.node_from.node_id),
            "to_node": str(self.node_to.node_id),
            "legal_context": LegalContext.NATIONALIZATION,
            "items": [{"sku": "SKU-LIFE", "quantity": 100}]
        }
        res = self.client.post("/api/transfers/create/", payload, format='json')
        trf_id = res.json()["transfer_id"]
        
        # 2. APPROVE (C31)
        res = self.client.post(f"/api/transfers/{trf_id}/approve/")
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["status"] == TransferStatus.APPROVED
        
        # 3. DISPATCH (C32)
        res = self.client.post(f"/api/transfers/{trf_id}/dispatch/")
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["status"] == TransferStatus.IN_TRANSIT
        
        # 4. RECEIVE (C33)
        receive_payload = {
            "lines": [
                {"sku": "SKU-LIFE", "quantity_received": 95, "condition": "good"} # Discrepancy of 5!
            ]
        }
        res = self.client.post(f"/api/transfers/{trf_id}/receive/", receive_payload, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["status"] == TransferStatus.RECEIVED
        
        # Verify line received data
        line = TransferLine.objects.get(transfer__transfer_id=trf_id, sku="SKU-LIFE")
        assert line.quantity_received == 95
        assert line.has_discrepancy is True
        
        # 5. RECONCILE (C34) - exception required since there is a discrepancy.
        self.client.force_authenticate(user=self.admin_user)
        reconcile_payload = {"exception_reason": "5 boxes lost during transit."}
        res = self.client.post(f"/api/transfers/{trf_id}/reconcile/", reconcile_payload, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.json()["status"] == TransferStatus.RECONCILED
        
        trf = Transfer.objects.get(transfer_id=trf_id)
        assert trf.exception_reason == "5 boxes lost during transit."
        assert trf.reconciled_at is not None

    def test_c35_cancel_transfer(self):
        self.client.force_authenticate(user=self.admin_user)
        
        # Create transfer
        payload = {
            "from_node": str(self.node_from.node_id),
            "to_node": str(self.node_to.node_id),
            "legal_context": LegalContext.INTERNAL,
            "items": [{"sku": "SKU-CANCEL", "quantity": 10}]
        }
        res = self.client.post("/api/transfers/create/", payload, format='json')
        trf_id = res.json()["transfer_id"]
        
        # Cancel
        res = self.client.post(f"/api/transfers/{trf_id}/cancel/", {"reason": "Change of plans"}, format='json')
        assert res.status_code == status.HTTP_200_OK
        
        trf = Transfer.objects.get(transfer_id=trf_id)
        assert trf.status == TransferStatus.CANCELLED
        assert trf.cancel_reason == "Change of plans"

    def test_c35_cancel_forbidden_after_dispatch(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "from_node": str(self.node_from.node_id),
            "to_node": str(self.node_to.node_id),
            "legal_context": LegalContext.INTERNAL,
            "items": [{"sku": "SKU-BAD-CANCEL", "quantity": 10}]
        }
        res = self.client.post("/api/transfers/create/", payload, format='json')
        trf_id = res.json()["transfer_id"]
        
        self.client.post(f"/api/transfers/{trf_id}/approve/")
        self.client.post(f"/api/transfers/{trf_id}/dispatch/")
        
        # Attempt cancel
        try:
            res = self.client.post(f"/api/transfers/{trf_id}/cancel/", {"reason": "Oops"}, format='json')
            assert res.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        except ValueError as e:
            assert "only be cancelled from planned or approved" in str(e)
