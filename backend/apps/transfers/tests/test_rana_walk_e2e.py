from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.transfers.models import Transfer, Node
from apps.expedientes.models import Expediente, ArtifactInstance, LegalEntity
from apps.expedientes.enums_exp import ExpedienteStatus
from apps.expedientes.tests.factories import create_user, create_expediente, create_legal_entity

class RanaWalkE2ETests(APITestCase):

    def setUp(self):
        self.ceo = create_user(username='ceo', is_superuser=True)
        self.client.force_authenticate(user=self.ceo)
        self.le = create_legal_entity(entity_id='RW_CORP')
        
        self.node_origin = Node.objects.create(name="Origin", legal_entity=self.le, node_type="factory", location="CR")
        self.node_dest = Node.objects.create(name="Dest", legal_entity=self.le, node_type="warehouse", location="US")

    def test_rana_walk_flow_to_closed(self):
        # 1. Create Expediente Rana Walk
        expediente = create_expediente(client=self.le, brand='RANA_WALK', status=ExpedienteStatus.PLANIFICACION)
        
        # 2. Transfer Planned
        url_create_transfer = reverse('transfers:create')
        res = self.client.post(url_create_transfer, {
            "from_node": self.node_origin.id,
            "to_node": self.node_dest.id,
            "legal_context": "INTERNAL",
            "source_expediente": expediente.id,
            "items": [{"sku": "RW-GOL-41", "quantity": 100}]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        transfer_id = res.data['transfer_id']

        # 3. Create Preparation Artifact (ART-14) (C37)
        url_prep = reverse('transfers:complete_preparation', kwargs={'transfer_id': transfer_id})
        res = self.client.post(url_prep, {
            "payload": {
                "actions": [{"action_type": "packaging", "description": "Boxed", "quantity_affected": 100}],
                "prepared_by": "Worker 1",
                "prepared_at": "2026-03-01T10:00:00Z",
                "notes": "All prep done"
            }
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 4. Approve Transfer (C31)
        url_approve = reverse('transfers:approve', kwargs={'transfer_id': transfer_id})
        res = self.client.post(url_approve)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 5. Create Dispatch Artifact (ART-15) (C38)
        url_dispatch = reverse('transfers:complete_dispatch', kwargs={'transfer_id': transfer_id})
        res = self.client.post(url_dispatch, {
            "payload": {
                "carrier": "FedEx",
                "tracking_number": "123456789",
                "dispatched_by": "Worker 2"
            }
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 6. Create Reception Artifact (ART-13) (C36)
        url_receive = reverse('transfers:complete_reception', kwargs={'transfer_id': transfer_id})
        res = self.client.post(url_receive, {
            "lines": [{"sku": "RW-GOL-41", "quantity_received": 100}],
            "payload": {
                "received_by": "Worker 3",
                "notes": "Received in good condition"
            }
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # 7. Check final states
        transfer = Transfer.objects.get(transfer_id=transfer_id)
        self.assertEqual(transfer.status, "received")
        
        art14 = ArtifactInstance.objects.filter(expediente=expediente, artifact_type='ART-14').exists()
        art15 = ArtifactInstance.objects.filter(expediente=expediente, artifact_type='ART-15').exists()
        art13 = ArtifactInstance.objects.filter(expediente=expediente, artifact_type='ART-13').exists()
        
        self.assertTrue(art14)
        self.assertTrue(art15)
        self.assertTrue(art13)

