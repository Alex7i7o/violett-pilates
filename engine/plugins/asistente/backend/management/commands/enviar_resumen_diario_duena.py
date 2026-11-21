import datetime
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Turno, Reserva
from plugins.comunicaciones.backend.whatsapp_service import (
    WhatsAppClient,
    obtener_telefono_duena,
    obtener_telefonos_staff_alertas,
    _registrar_log_saliente
)
from ...models import RegistroAccionIA
from ...tools.profesores_tools import obtener_profesor_de_turno

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Envía el resumen diario ejecutivo de la jornada y anticipo de mañana a Débora por WhatsApp (21:05 hs)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--forzar',
            action='store_true',
            help="Forzar envío ignorando si ya fue enviado hoy"
        )

    def handle(self, *args, **options):
        forzar = options['forzar']

        tel_duena = obtener_telefono_duena()
        if not tel_duena:
            self.stdout.write(self.style.ERROR("No se encontró teléfono de la dueña configurado."))
            return

        hoy = timezone.localdate()
        manana = hoy + datetime.timedelta(days=1)

        dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        dia_hoy_nom = dias_es[hoy.weekday()]
        dia_manana_nom = dias_es[manana.weekday()]

        tag_dia = f"resumen_nocturno_duena_{hoy.isoformat()}"

        if not forzar:
            ya_enviado = RegistroAccionIA.objects.filter(
                tipo_accion='REPORTE_DUENA',
                payload__tag=tag_dia
            ).exists()
            if ya_enviado:
                self.stdout.write(f"✦ El resumen de hoy ya fue enviado previamente. Usa --forzar para re-enviar.")
                return

        # 1. BALANCE DE HOY
        turnos_hoy = Turno.objects.filter(fecha=hoy).select_related('clase')
        total_clases_hoy = turnos_hoy.count()
        clases_dictadas = turnos_hoy.filter(estado__in=['COMPLETADO', 'PROGRAMADO']).count()
        clases_canceladas_hoy = turnos_hoy.filter(estado='CANCELADO').count()

        reservas_hoy = Reserva.objects.filter(turno__fecha=hoy)
        asistencias_hoy = reservas_hoy.filter(estado__in=['TOMADA', 'CONFIRMADA']).count()
        bajas_hoy = reservas_hoy.filter(estado__in=['CANCELADA_TIEMPO', 'CANCELADA_TARDIA', 'CANCELADA']).count()

        # 2. ANTICIPO DE MAÑANA
        turnos_manana = Turno.objects.filter(fecha=manana, estado='PROGRAMADO').select_related('clase').order_by('hora_inicio')
        total_clases_manana = turnos_manana.count()

        alertas_manana = []
        cupo_total_ocupado = 0
        cupo_total_disponible = 0
        cronograma_manana = []

        for t in turnos_manana:
            prof = obtener_profesor_de_turno(t)
            prof_nom = prof.nombre if prof and hasattr(prof, 'nombre') else "Sin asignar"
            clase_max = t.clase.cupo_maximo if t.clase else 4
            inscriptas = t.reservas.filter(estado='CONFIRMADA').count()
            libres = t.cupo_actual

            cupo_total_ocupado += inscriptas
            cupo_total_disponible += libres

            h_str = t.hora_inicio.strftime('%H:%M')
            cronograma_manana.append(f"• {h_str} hs: {inscriptas}/{clase_max} camillas ({prof_nom})")

            if inscriptas == 1:
                alertas_manana.append(f"⚠ {h_str} hs tiene solo 1 alumna inscripta.")
            elif inscriptas == 0:
                alertas_manana.append(f"ℹ {h_str} hs está vacía (0 alumnas).")
            if not prof or prof_nom == "Sin asignar":
                alertas_manana.append(f"🚨 {h_str} hs no tiene profesor confirmado.")

        crono_txt = "\n".join(cronograma_manana) if cronograma_manana else "• No hay clases programadas para mañana."
        alertas_txt = "\n".join(alertas_manana) if alertas_manana else "• ¡Todo en orden, sin alertas críticas! ✨"

        texto = (
            f"✦ *Resumen Ejecutivo Nocturno — Violett Pilates* ✦\n"
            f"📅 *{dia_hoy_nom} {hoy.strftime('%d/%m')}*\n\n"
            f"📊 *Balance del Día:* \n"
            f"• Clases en grilla: {clases_dictadas} dictadas" + (f" ({clases_canceladas_hoy} canceladas)" if clases_canceladas_hoy else "") + f"\n"
            f"• Alumnas en sala: {asistencias_hoy} asistencias registradas\n"
            f"• Cancelaciones de alumnas: {bajas_hoy}\n\n"
            f"🌅 *Anticipo para Mañana ({dia_manana_nom} {manana.strftime('%d/%m')}):*\n"
            f"• Clases programadas: {total_clases_manana}\n"
            f"• Camillas ocupadas: {cupo_total_ocupado} (libres: {cupo_total_disponible})\n\n"
            f"📋 *Cronograma de Mañana:*\n"
            f"{crono_txt}\n\n"
            f"🔔 *Alertas y Puntos de Atención:*\n"
            f"{alertas_txt}\n\n"
            f"¡Que descanses Deby! Mañana seguimos acompañando tu estudio 🌸."
        )

        client = WhatsAppClient()
        for t_dest in obtener_telefonos_staff_alertas():
            try:
                client.send_text_message(t_dest, texto)
                _registrar_log_saliente(t_dest, None, texto, "resumen_nocturno_duena")
            except Exception as e_send:
                logger.error(f"Error enviando resumen diario a {t_dest}: {e_send}")

        RegistroAccionIA.objects.create(
            tipo_accion='REPORTE_DUENA',
            descripcion=f"Resumen diario ejecutivo de la jornada {hoy.isoformat()} y anticipo de mañana.",
            payload={'tag': tag_dia, 'fecha': hoy.isoformat(), 'total_asistencias': asistencias_hoy, 'clases_manana': total_clases_manana}
        )

        self.stdout.write(self.style.SUCCESS(f"✓ Resumen diario nocturno enviado con éxito a la Dirección."))
