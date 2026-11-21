import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Turno
from ...tools.profesores_tools import obtener_profesor_de_turno

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = (
        "Revisa las clases de los próximos 7 días (1 semana) y le notifica a Débora por WhatsApp "
        "en un único resumen consolidado aquellas que tengan solo 1 alumna inscripta."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=7,
            help="Ventana de días hacia adelante a evaluar (default: 7 días / 1 semana)"
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help="Forzar envío ignorando deduplicación de 20hs"
        )

    def handle(self, *args, **options):
        dias_adelante = options['dias']
        forzar = options.get('forzar', False)
        now = timezone.localtime()
        tz = now.tzinfo
        limite_dt = now + datetime.timedelta(days=dias_adelante)

        self.stdout.write(
            f"✦ [REVISIÓN CLASES 1 ALUMNA] Buscando turnos entre {now.strftime('%d/%m')} "
            f"y {limite_dt.strftime('%d/%m')} con exactamente 1 alumna..."
        )

        turnos = Turno.objects.filter(
            estado='PROGRAMADO',
            fecha__gte=now.date(),
            fecha__lte=limite_dt.date()
        ).select_related('clase').order_by('fecha', 'hora_inicio')

        evaluados = 0
        clases_una_alumna = []
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

        for turno in turnos:
            clase_dt = datetime.datetime.combine(turno.fecha, turno.hora_inicio)
            if timezone.is_naive(clase_dt):
                clase_dt = timezone.make_aware(clase_dt, tz)

            if clase_dt <= now or clase_dt > limite_dt:
                continue

            evaluados += 1
            res_conf = turno.reservas.filter(estado='CONFIRMADA').select_related('usuario')
            if res_conf.count() == 1:
                res = res_conf.first()
                u = res.usuario
                alumna_nom = f"{u.nombre} {u.apellido}".strip() if u else (res.nombre_temporal or "Alumna puntual")
                dia_nom = dias_semana[turno.fecha.weekday()]
                fecha_str = turno.fecha.strftime('%d/%m')
                hora_str = turno.hora_inicio.strftime('%H:%M')
                prof = obtener_profesor_de_turno(turno)
                prof_nom = f" (Prof. {prof.nombre})" if prof and hasattr(prof, 'nombre') else ""
                clases_una_alumna.append(f"• *{dia_nom} {fecha_str} a las {hora_str} hs*{prof_nom} — {alumna_nom} (2 camillas libres)")

        if clases_una_alumna:
            from plugins.comunicaciones.backend.whatsapp_service import WhatsAppClient, obtener_telefono_duena, _registrar_log_saliente
            from ...models import RegistroAccionIA, ConversacionWhatsApp, MensajeWhatsAppLog

            tel_duena = obtener_telefono_duena()
            if tel_duena:
                hace_20h = now - datetime.timedelta(hours=20)
                ya_enviado = RegistroAccionIA.objects.filter(
                    tipo_accion='ALERTA_CLASE_UNA_ALUMNA',
                    created_at__gte=hace_20h,
                    payload__consolidado=True
                ).exists()

                if not ya_enviado or forzar:
                    lista_txt = "\n".join(clases_una_alumna)
                    msg = (
                        f"¡Hola Deby! ✦ Alerta de Agenda Semanal:\n\n"
                        f"Las siguientes clases de los próximos 7 días tienen *solo 1 alumna inscripta*:\n\n"
                        f"{lista_txt}\n\n"
                        f"Quedan camillas libres para promocionar o evaluar si conviene reubicar ✨."
                    )
                    client = WhatsAppClient()
                    client.send_text_message(tel_duena, msg)
                    _registrar_log_saliente(tel_duena, None, msg, "alerta_clase_una_alumna")

                    conv, _ = ConversacionWhatsApp.objects.get_or_create(telefono=tel_duena)
                    MensajeWhatsAppLog.objects.create(
                        conversacion=conv,
                        direccion='SALIENTE',
                        agente_responsable='alerta_clase_una_alumna',
                        texto=msg,
                        tools_ejecutadas=['resumen_semanal_una_alumna']
                    )
                    RegistroAccionIA.objects.create(
                        conversacion=conv,
                        tipo_accion='ALERTA_CLASE_UNA_ALUMNA',
                        descripcion=f"Resumen semanal de clases con 1 alumna enviado ({len(clases_una_alumna)} clases).",
                        payload={'consolidado': True, 'cantidad': len(clases_una_alumna)}
                    )
                    self.stdout.write(self.style.SUCCESS(f"✓ Resumen semanal enviado a Deby con {len(clases_una_alumna)} clases."))
                else:
                    self.stdout.write(self.style.WARNING("⏳ Resumen semanal ya enviado en las últimas 20hs. Omitiendo reenvío."))

        self.stdout.write(
            self.style.SUCCESS(
                f"✦ [FINALIZADO] Turnos evaluados: {evaluados} | Clases con 1 alumna detectadas: {len(clases_una_alumna)}"
            )
        )
