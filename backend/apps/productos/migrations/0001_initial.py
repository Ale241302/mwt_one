# Generated manually — Sprint 11 fix
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('brands', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('sku_base', models.CharField(help_text='SKU base del producto', max_length=50, unique=True)),
                ('category', models.CharField(blank=True, max_length=100)),
                ('description', models.TextField(blank=True)),
                ('brand', models.ForeignKey(
                    on_delete=django.db.models.deletion.PROTECT,
                    related_name='productos',
                    to='brands.brand',
                )),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
                'db_table': 'productos_producto',
                'ordering': ['name'],
            },
        ),
    ]
