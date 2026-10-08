from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetricaInteractiva',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tipo', models.CharField(choices=[('EMAIL', 'Email Enviado'), ('WPP', 'WhatsApp Enviado'), ('AUTO_RESERVA', 'Reserva Auto-gestionada'), ('AUTO_CANCEL', 'Cancelación Auto-gestionada')], max_length=20)),
                ('fecha', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.usuario')),
            ],
            options={
                'db_table': 'plugin_analitica_metricas',
            },
        ),
        migrations.CreateModel(
            name='RegistroFacturacion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('fecha', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ('plan_nombre', models.CharField(max_length=100)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=12)),
                ('suscripcion_id', models.CharField(blank=True, max_length=100, null=True)),
                ('usuario', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.usuario')),
            ],
            options={
                'db_table': 'plugin_analitica_facturacion',
            },
        ),
    ]
