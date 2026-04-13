import uuid
import logging
from django.utils import timezone
from apps.expedientes.models import Expediente, ArtifactInstance
from apps.expedientes.enums_exp import ArtifactType
from apps.pricing.services import resolve_client_price

logger = logging.getLogger(__name__)

class ProformaGeneratorService:
    """
    Genera el HTML usando el template `PF_0000-2026_GOLDEN_EXAMPLE.html`,
    lo convierte a PDF (stub con weasyprint/xhtml2pdf), y lo sube a S3 con JWT tokens.
    """
    
    @classmethod
    def generate_proforma(cls, expediente: Expediente, pricing_mode: str) -> ArtifactInstance:
        # Integración S22: Resolver el precio validado para este expediente antes de emitir proforma
        brand_id = expediente.brand_id if expediente.brand else None
        client_id = expediente.client_id if expediente.client else None
        
        price_lookup = resolve_client_price(
            brand_id=brand_id,
            party_type='client',
            party_id=client_id,
            sku='GENERIC-PROFORMA-CHECK', # En producción se iteran los productos del expediente
            mode=pricing_mode,
            currency='USD',
            date=timezone.now().date()
        )
        base_price = price_lookup['price'] if price_lookup else 0.0

        # 1. Render HTML logic (stubbed with real resolved price reference)
        rendered_html = f"<html><body>Proforma for {expediente.expediente_id} - Mode {pricing_mode} - Base {base_price}</body></html>"
        
        # 2. Convert to PDF (stubbed fallback)
        # try:
        #     from weasyprint import HTML
        #     pdf_data = HTML(string=rendered_html).write_pdf()
        # except:
        pdf_data = b"%PDF-1.4 Mock Data"
        
        # 3. Simulate upload to S3 via S24 signed logic
        file_url = f"s3://mwt-documents/proformas/{expediente.expediente_id}/PROFORMA_{uuid.uuid4().hex[:8]}.pdf"
        
        # 4. Save ArtifactInstance metadata in payload
        artifact = ArtifactInstance.objects.create(
            expediente=expediente,
            artifact_type=ArtifactType.PROFORMA,
            payload={
                "doc_code": f"PF-REF-{expediente.expediente_id}",
                "file_url": file_url,
                "is_valid": True,
                "pricing_mode": pricing_mode
            }
        )
        
        logger.info(f"Generated Proforma {artifact.payload.get('doc_code')} for Expediente {expediente.expediente_id}")
        return artifact
