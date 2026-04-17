"""
S26-06: Servicios de resolución de destinatarios, template, y contexto.

resolve_notification_recipient() — para notificaciones transaccionales
resolve_collection_recipient() — para cobranza (usa proforma del pago)
resolve_template() — busca template con fallback
build_notification_context() — contexto Jinja2 para render
"""
from apps.core.registry import ModuleRegistry
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Template resolution
# =============================================================================

def resolve_template(template_key: str, brand, language: str = 'es'):
    """
    Busca NotificationTemplate con fallback en 3 pasos:
    1. (template_key, brand, language)
    2. (template_key, brand=null, language)
    3. (template_key, brand=null, 'es')
    Usa .filter().first() — nunca .get() para evitar MultipleObjectsReturned.
    """
    template_model = ModuleRegistry.get_model('notifications', 'NotificationTemplate')
    if not template_model:
        return None

    if brand is not None:
        # 1. Buscar override específico por brand + language
        tpl = NotificationTemplate.objects.filter(
            template_key=template_key,
            brand=brand,
            language=language,
            is_active=True,
        ).first()
        if tpl:
            return tpl

    # 2. Fallback default (brand=null) + language
    tpl = NotificationTemplate.objects.filter(
        template_key=template_key,
        brand__isnull=True,
        language=language,
        is_active=True,
    ).first()
    if tpl:
        return tpl

    # 3. Fallback default (brand=null) + 'es'
    if language != 'es':
        tpl = NotificationTemplate.objects.filter(
            template_key=template_key,
            brand__isnull=True,
            language='es',
            is_active=True,
        ).first()
        if tpl:
            return tpl

    logger.warning(f"[NOTIF] Template not found: key={template_key} brand={brand} lang={language}")
    return None


# =============================================================================
# Recipient resolution — notificaciones transaccionales
# =============================================================================

def resolve_notification_recipient(expediente, proforma_id=None) -> str | None:
    """
    Mode C (operado por MWT) → CEO_EMAIL.
    Mode B (operado por cliente) → client contact_email.
    """
    mode = _resolve_mode(expediente, proforma_id)

    if mode == 'C':
        ceo_email = getattr(settings, 'CEO_EMAIL', '') or None
        if not ceo_email:
            logger.warning("[NOTIF] CEO_EMAIL not configured — Mode C notification skipped")
        return ceo_email
    else:
        # Mode B: email del contacto del cliente
        subsidiary = getattr(expediente, 'client_subsidiary', None)
        if subsidiary:
            email = getattr(subsidiary, 'contact_email', None)
            if email:
                return email

        # Fallback: buscar en ClientSubsidiary por client (LegalEntity)
        try:
            subsidiary_model = ModuleRegistry.get_model('clientes', 'ClientSubsidiary')
            subsidiary = subsidiary_model.objects.filter(
                legal_entity=expediente.client,
                is_active=True,
                contact_email__isnull=False,
            ).exclude(contact_email='').first()
            if subsidiary:
                return subsidiary.contact_email
        except Exception:
            pass

        logger.warning(f"[NOTIF] No contact_email for expediente={expediente.pk}")
        return None


def resolve_collection_recipient(pago) -> tuple:
    """
    Resuelve destinatario para email de cobranza.
    """
    mode = 'B'
    proforma = None

    # Verificar FK proforma en el modelo vía introspección
    pago_field_names = {f.name for f in pago.__class__._meta.get_fields()}
    if 'proforma' in pago_field_names:
        proforma = getattr(pago, 'proforma', None)
        if proforma is not None and hasattr(proforma, 'metadata') and proforma.metadata:
            mode = proforma.metadata.get('mode', 'B')

    if mode == 'C':
        ceo_email = getattr(settings, 'CEO_EMAIL', '') or None
        return ceo_email, proforma
    else:
        subsidiary = getattr(pago.expediente, 'client_subsidiary', None)
        if subsidiary:
            contact = getattr(subsidiary, 'contact_email', None)
            if contact:
                return contact, proforma

        # Fallback: buscar vía LegalEntity
        try:
            subsidiary_model = ModuleRegistry.get_model('clientes', 'ClientSubsidiary')
            subsidiary = subsidiary_model.objects.filter(
                legal_entity=pago.expediente.client,
                is_active=True,
                contact_email__isnull=False,
            ).exclude(contact_email='').first()
            if subsidiary:
                return subsidiary.contact_email, proforma
        except Exception:
            pass

        logger.warning(f"[COLLECTION] No contact_email for pago={pago.pk}")
        return None, proforma


# =============================================================================
# Internal helper
# =============================================================================

def _resolve_mode(expediente, proforma_id=None) -> str:
    """
    Determina el modo (C/B) a partir de proforma_id o de las proformas del expediente.
    """
    artifact_model = ModuleRegistry.get_model('expedientes', 'ArtifactInstance')
    if not artifact_model:
        return 'B'

    if proforma_id:
        try:
            proforma = artifact_model.objects.get(pk=proforma_id)
            return proforma.payload.get('mode', 'B')
        except artifact_model.DoesNotExist:
            return 'B'
    else:
        # Revisar proformas del expediente (ART-02)
        proformas = list(
            expediente.artifacts.filter(artifact_type='ART-02')
            .values_list('payload', flat=True)
        )
        if proformas and all(p.get('mode') == 'C' for p in proformas if isinstance(p, dict)):
            return 'C'
        return 'B'


# =============================================================================
# Context builder — variables disponibles en templates Jinja2
# =============================================================================

def build_notification_context(expediente, proforma_id=None, extra_context=None) -> dict:
    """
    Construye el contexto de variables para render de templates Jinja2.
    """
    artifact_model = ModuleRegistry.get_model('expedientes', 'ArtifactInstance')

    # client.name desde LegalEntity
    client_name = getattr(expediente.client, 'legal_name', None) or \
                  getattr(expediente.client, 'name', 'Cliente')

    ctx = {
        'expediente_code': str(expediente.expediente_id)[:8].upper(),
        'client_name': client_name,
        'brand_name': expediente.brand.name if expediente.brand else 'N/A',
        'current_status': getattr(expediente, 'status', 'N/A'),
        'portal_url': f"{getattr(settings, 'PORTAL_BASE_URL', 'https://portal.mwt.one')}/expedientes/{expediente.pk}",
        'mwt_signature': 'Muito Work Limitada — Gestión Comercial B2B',
    }

    if proforma_id and artifact_model:
        try:
            proforma = artifact_model.objects.get(pk=proforma_id)
            ctx['proforma_number'] = proforma.payload.get('number', 'N/A')
            ctx['proforma_mode'] = proforma.payload.get('mode', 'N/A')
        except artifact_model.DoesNotExist:
            pass

    if extra_context:
        ctx.update(extra_context)

    return ctx
