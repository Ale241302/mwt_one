import os

filepath = 'apps/expedientes/tests/test_commands.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix C2 Artifact
content = content.replace("artifact_type='OC'", "artifact_type='ART-01'")

# Fix C7
content = content.replace(
    "def test_c7_register_shipment_starts_clock(self):\n        self.exp.status = ExpedienteStatus.PRODUCCION\n",
    "def test_c7_register_shipment_starts_clock(self):\n        self.exp.status = ExpedienteStatus.PREPARACION\n        ArtifactInstance.objects.create(expediente=self.exp, artifact_type='ART-04', status='completed')\n"
)

# Fix C8
content = content.replace(
    "def test_c8_register_freight_quote(self):\n        self.exp.status = ExpedienteStatus.PRODUCCION\n",
    "def test_c8_register_freight_quote(self):\n        self.exp.status = ExpedienteStatus.PREPARACION\n"
)

# Fix C10
c10_old = "ArtifactInstance.objects.create(expediente=self.exp, artifact_type='ART-06', status='completed')"
c10_new = "ArtifactInstance.objects.create(expediente=self.exp, artifact_type='ART-06', status='completed')\n        ArtifactInstance.objects.create(expediente=self.exp, artifact_type='ART-08', status='completed')"
content = content.replace(c10_old, c10_new)

# Fix C12
content = content.replace(
    "def test_c12_confirm_arrival(self):\n        self.exp.status = ExpedienteStatus.DESPACHO\n",
    "def test_c12_confirm_arrival(self):\n        self.exp.status = ExpedienteStatus.TRANSITO\n"
)

# Fix C13
content = content.replace(
    "def test_c13_issue_invoice(self):\n        self.exp.status = ExpedienteStatus.DESPACHO\n",
    "def test_c13_issue_invoice(self):\n        self.exp.status = ExpedienteStatus.EN_DESTINO\n"
)

# Fix C14 fails
content = content.replace(
    "def test_c14_close_fails_if_unpaid(self):\n        self.exp.status = ExpedienteStatus.DESPACHO\n",
    "def test_c14_close_fails_if_unpaid(self):\n        self.exp.status = ExpedienteStatus.EN_DESTINO\n"
)

# Fix C14 success
content = content.replace(
    "def test_c14_close_success(self):\n        self.exp.status = ExpedienteStatus.DESPACHO\n",
    "def test_c14_close_success(self):\n        self.exp.status = ExpedienteStatus.EN_DESTINO\n"
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done fixing test states!')
