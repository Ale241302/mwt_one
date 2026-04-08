# S25-02: AddField ×4 en Expediente — deferred_total_price, deferred_visible,
#          parent_expediente (self-FK), is_inverted_child.
# SOLO AddField — sin data migration (campos nullable/default).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expedientes', '0024_migrate_legacy_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='expediente',
            name='deferred_total_price',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text=(
                    "Precio diferido del expediente. Uso interno CEO. "
                    "Equivale a 'order_full_price_diferido' del sistema viejo. "
                    "NULL = no definido. Editable solo por CEO."
                ),
                max_digits=14,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='expediente',
            name='deferred_visible',
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Si True, el precio diferido es visible en el portal del cliente. "
                    "Por default invisible (solo CEO). Toggle manual."
                ),
            ),
        ),
        migrations.AddField(
            model_name='expediente',
            name='parent_expediente',
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text='Expediente padre (origen de un split). NULL = expediente original.',
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='child_expedientes',
                to='expedientes.expediente',
            ),
        ),
        migrations.AddField(
            model_name='expediente',
            name='is_inverted_child',
            field=models.BooleanField(
                default=False,
                help_text=(
                    "True si este expediente fue creado por split con inversión: "
                    "el 'nuevo' expediente tomó el rol de padre y el 'original' se convirtió en hijo. "
                    "Informativo para el CEO — no afecta lógica de negocio."
                ),
            ),
        ),
    ]
