from django.db import migrations

def normalizar_canceladas(apps, schema_editor):
    Reserva = apps.get_model('core', 'Reserva')
    # Normalizar cualquier reserva con estado 'CANCELADA' a 'CANCELADA_TIEMPO'
    Reserva.objects.filter(estado='CANCELADA').update(estado='CANCELADA_TIEMPO')

def reverse_normalizar(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_reserva_unique_together_and_more'),
    ]

    operations = [
        migrations.RunPython(normalizar_canceladas, reverse_normalizar),
    ]
