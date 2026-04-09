"""
S26-03: Data migration — 10 templates seed.
get_or_create por template_key+brand+language. Idempotente: 2x → 10 templates, no 20.
"""
from django.db import migrations


SEED_TEMPLATES = [
    {
        'template_key': 'expediente.registered',
        'name': 'Registro de expediente',
        'subject_template': 'Expediente {{ expediente_code }} registrado',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'Le informamos que el expediente {{ expediente_code }} ha sido registrado exitosamente en nuestra plataforma.\n\n'
            'Puede consultar el estado en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
    {
        'template_key': 'expediente.production_started',
        'name': 'Producción iniciada',
        'subject_template': 'Producción iniciada — {{ expediente_code }}',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'La producción del expediente {{ expediente_code }} ha iniciado.\n\n'
            'Puede hacer seguimiento en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
    {
        'template_key': 'expediente.dispatched',
        'name': 'Despacho confirmado',
        'subject_template': 'Despacho confirmado — {{ expediente_code }}',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'El expediente {{ expediente_code }} ha sido despachado.\n\n'
            'Consulte detalles en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
    {
        'template_key': 'expediente.in_transit',
        'name': 'En tránsito',
        'subject_template': 'En tránsito — {{ expediente_code }}',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'El expediente {{ expediente_code }} se encuentra en tránsito hacia su destino.\n\n'
            'Seguimiento en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
    {
        'template_key': 'expediente.delivered',
        'name': 'Entrega confirmada',
        'subject_template': 'Entrega confirmada — {{ expediente_code }}',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'El expediente {{ expediente_code }} ha sido entregado exitosamente.\n\n'
            'Verifique en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
    {
        'template_key': 'payment.verified',
        'name': 'Pago verificado',
        'subject_template': 'Pago verificado — {{ expediente_code }}',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'Su pago para el expediente {{ expediente_code }} ha sido verificado correctamente.\n\n'
            'Detalle en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
    {
        'template_key': 'payment.rejected',
        'name': 'Pago rechazado',
        'subject_template': 'Pago rechazado — {{ expediente_code }}',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'Lamentamos informarle que el pago del expediente {{ expediente_code }} ha sido rechazado.\n\n'
            'Por favor contáctenos para regularizar la situación.\n'
            'Detalle en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
    {
        'template_key': 'payment.credit_released',
        'name': 'Crédito liberado',
        'subject_template': 'Crédito liberado — {{ expediente_code }}',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'El crédito del expediente {{ expediente_code }} ha sido liberado.\n\n'
            'Consulte su estado en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
    {
        'template_key': 'payment.overdue',
        'name': 'Pago vencido (cobranza)',
        'subject_template': 'Pago vencido — {{ expediente_code }}',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'Le informamos que tiene un pago vencido en el expediente {{ expediente_code }}.\n\n'
            'Monto vencido: {{ pago_amount }}\n'
            'Días de gracia utilizados: {{ grace_days }}\n\n'
            'Por favor regularice su situación en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
    {
        'template_key': 'proforma.sent',
        'name': 'Proforma enviada',
        'subject_template': 'Proforma {{ proforma_number }} — {{ brand_name }}',
        'body_template': (
            'Estimado {{ client_name }},\n\n'
            'Adjuntamos la proforma {{ proforma_number }} de {{ brand_name }}.\n\n'
            'Puede acceder a los detalles en: {{ portal_url }}\n\n'
            '{{ mwt_signature }}'
        ),
    },
]


def seed_templates(apps, schema_editor):
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    for tpl in SEED_TEMPLATES:
        NotificationTemplate.objects.get_or_create(
            template_key=tpl['template_key'],
            brand=None,
            language='es',
            defaults={
                'name': tpl['name'],
                'subject_template': tpl['subject_template'],
                'body_template': tpl['body_template'],
                'is_active': True,
            }
        )


def unseed_templates(apps, schema_editor):
    """Reversible: elimina solo los seeds con brand=null, language='es'."""
    NotificationTemplate = apps.get_model('notifications', 'NotificationTemplate')
    keys = [t['template_key'] for t in SEED_TEMPLATES]
    NotificationTemplate.objects.filter(
        template_key__in=keys,
        brand=None,
        language='es',
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_templates, reverse_code=unseed_templates),
    ]
