import uuid
import logging
from django.utils import timezone
from apps.expedientes.models import Expediente, ArtifactInstance
from apps.expedientes.enums_artifacts import ArtifactType

logger = logging.getLogger(__name__)

class ProformaGeneratorService:
    """
    Genera el HTML usando el template `PF_0000-2026_GOLDEN_EXAMPLE.html`,
    lo convierte a PDF (stub con weasyprint/xhtml2pdf), y lo sube a S3 con JWT tokens.
    """
    
    @classmethod
    def generate_proforma(cls, expediente: Expediente, pricing_mode: str) -> ArtifactInstance:
        # Aquí se integraría con resolve_client_price de S22
        # resolve_client_price(brand_id=..., party_id=... mode=pricing_mode)
        
        # 1. Render HTML logic (stubbed)
        rendered_html = f"<html><body>Proforma for {expediente.expediente_id} - Mode {pricing_mode}</body></html>"
        
        # 2. Convert to PDF (stubbed fallback)
        # try:
        #     from weasyprint import HTML
        #     pdf_data = HTML(string=rendered_html).write_pdf()
        # except:
        pdf_data = b"%PDF-1.4 Mock Data"
        
        # 3. Simulate upload to S3 via S24 signed logic
        file_url = f"s3://mwt-documents/proformas/{expediente.expediente_id}/PROFORMA_{uuid.uuid4().hex[:8]}.pdf"
        
        # 4. Save ArtifactInstance metadata
        artifact = ArtifactInstance.objects.create(
            expediente=expediente,
            artifact_type=ArtifactType.PROFORMA,
            doc_code=f"PF-{expediente.expediente_id}-{timezone.now().year}",
            file_url=file_url,
            is_valid=True
        )
        
        logger.info(f"Generated Proforma {artifact.doc_code} for Expediente {expediente.expediente_id}")
        return artifact
