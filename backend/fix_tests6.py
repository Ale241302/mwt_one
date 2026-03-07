import os

filepath_disp = 'apps/expedientes/tests/test_dispatcher.py'
with open(filepath_disp, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("from apps.expedientes.tasks import dispatch_events", "from apps.expedientes.tasks import process_pending_events")
content = content.replace("dispatch_events()", "process_pending_events()")

with open(filepath_disp, 'w', encoding='utf-8') as f:
    f.write(content)

filepath_cmd = 'apps/expedientes/tests/test_commands.py'
with open(filepath_cmd, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix mock:
# remove decorator `@patch('apps.expedientes.services.Expediente.save')`
# remove `mock_save` argument
# rewrite the method body
content = content.replace(
"""    @patch('apps.expedientes.services.Expediente.save')
    def test_atomicity_c5_transition_rollback(self, mock_save):
        mock_save.side_effect = Exception("Simulated Save Failure")
        self.exp.status = ExpedienteStatus.REGISTRO
        self.exp.save()""",
"""    def test_atomicity_c5_transition_rollback(self):
        self.exp.status = ExpedienteStatus.REGISTRO
        self.exp.save()"""
)

content = content.replace(
"""        url = reverse('expedientes:confirm-sap', kwargs={'pk': self.exp.pk})
        
        initial_events = EventLog.objects.count()
        with self.assertRaises(Exception):
            self.client.post(url, {'payload': {}}, format='json')""",
"""        url = reverse('expedientes:confirm-sap', kwargs={'pk': self.exp.pk})
        
        initial_events = EventLog.objects.count()
        with patch('apps.expedientes.services.Expediente.save') as mock_save:
            mock_save.side_effect = Exception("Simulated Save Failure")
            with self.assertRaises(Exception):
                self.client.post(url, {'payload': {}}, format='json')"""
)

with open(filepath_cmd, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done fixing test errors!")
