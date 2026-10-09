from django.db import migrations
from django.utils import timezone
import datetime

def backfill_facturacion(apps, schema_editor):
    try:
        Suscripcion = apps.get_model('membresias', 'Suscripcion')
    except LookupError:
        # Si el plugin membresias no est instalado o el modelo no existe, saltar
        return
        
    RegistroFacturacion = apps.get_model('analitica', 'RegistroFacturacion')
    
    # Iterate over all subscriptions and create a billing record if it doesn't exist
    for sub in Suscripcion.objects.select_related('plan', 'usuario').all():
        if not RegistroFacturacion.objects.filter(suscripcion_id=str(sub.id)).exists():
            # Convert DateField to DateTimeField safely
            if sub.fecha_inicio:
                dt_fecha = timezone.make_aware(datetime.datetime.combine(sub.fecha_inicio, datetime.time.min))
            else:
                dt_fecha = timezone.now()
                
            RegistroFacturacion.objects.create(
                usuario=sub.usuario,
                plan_nombre=sub.plan.nombre if sub.plan else "Plan Desconocido",
                monto=sub.plan.precio if sub.plan else 0,
                fecha=dt_fecha,
                suscripcion_id=str(sub.id)
            )

def reverse_backfill(apps, schema_editor):
    pass # No need to reverse

class Migration(migrations.Migration):

    dependencies = [
        ('analitica', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(backfill_facturacion, reverse_backfill),
    ]
