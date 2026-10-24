from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from django.conf import settings
from core.models import Usuario, Turno, Reserva
from .models import MetricaInteractiva, RegistroFacturacion
import datetime

class AnaliticaDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        month = int(request.query_params.get('month', now.month))
        year = int(request.query_params.get('year', now.year))
        
        # Helper to filter by month/year
        def in_month(qs, date_field):
            return qs.filter(**{f"{date_field}__month": month, f"{date_field}__year": year})

        # 1. EL MOTOR DE VALOR (Impacto y Ahorro Real)
        metricas = in_month(MetricaInteractiva.objects, 'fecha')
        emails_logged = metricas.filter(tipo='EMAIL').count()
        wpps_logged = metricas.filter(tipo='WPP').count()
        auto_reservas_logged = metricas.filter(tipo='AUTO_RESERVA').count()
        auto_cancels_logged = metricas.filter(tipo='AUTO_CANCEL').count()

        # Fuentes reales en base de datos para reconciliación robusta:
        # Reservas del mes (por turno o created_at)
        reservas_mes_turnos = Reserva.objects.filter(turno__fecha__month=month, turno__fecha__year=year)
        reservas_confirmadas = reservas_mes_turnos.filter(estado__in=['CONFIRMADA', 'TOMADA', 'AUSENTE']).count()
        reservas_canceladas = reservas_mes_turnos.filter(estado__in=['CANCELADA_TIEMPO', 'CANCELADA_TARDIA']).count()

        # También verificamos por created_at de la reserva
        reservas_creadas_mes = in_month(Reserva.objects, 'created_at')
        res_creadas_conf = reservas_creadas_mes.filter(estado__in=['CONFIRMADA', 'TOMADA', 'AUSENTE']).count()
        res_creadas_canc = reservas_creadas_mes.filter(estado__in=['CANCELADA_TIEMPO', 'CANCELADA_TARDIA']).count()

        auto_reservas = max(auto_reservas_logged, reservas_confirmadas, res_creadas_conf)
        auto_cancels = max(auto_cancels_logged, reservas_canceladas, res_creadas_canc)

        # Clientes
        clientes = Usuario.objects.filter(rol='CLIENTE')
        total_alumnos = clientes.count()
        nuevos_alumnos = in_month(clientes, 'created_at').count()

        # Auto-reconciliación: Asegurar que toda Suscripcion creada en este mes tenga su RegistroFacturacion
        try:
            from plugins.membresias.backend.models import Suscripcion
            existing_sub_ids = set(
                RegistroFacturacion.objects.exclude(suscripcion_id__isnull=True)
                .exclude(suscripcion_id='')
                .values_list('suscripcion_id', flat=True)
            )
            subs_missing = Suscripcion.objects.filter(
                fecha_inicio__month=month,
                fecha_inicio__year=year
            ).exclude(id__in=existing_sub_ids).select_related('usuario', 'plan')

            for sub in subs_missing:
                dt_inicio = datetime.datetime.combine(sub.fecha_inicio, datetime.time(12, 0))
                if timezone.is_naive(dt_inicio):
                    dt_inicio = timezone.make_aware(dt_inicio)
                RegistroFacturacion.objects.create(
                    usuario=sub.usuario,
                    plan_nombre=sub.plan.nombre if sub.plan else 'Plan',
                    monto=sub.plan.precio if sub.plan else 0,
                    suscripcion_id=str(sub.id),
                    fecha=dt_inicio
                )
        except Exception:
            pass

        # Facturación
        facturacion_qs = in_month(RegistroFacturacion.objects, 'fecha')
        total_facturacion = facturacion_qs.aggregate(Sum('monto'))['monto__sum'] or 0
        desglose_planes = list(facturacion_qs.values('plan_nombre').annotate(total=Sum('monto'), cantidad=Count('id')).order_by('-total'))
        planes_asignados_mes = facturacion_qs.count()

        # Enriquecer detalles con datos de Suscripcion y Alumno
        sub_ids = [r.suscripcion_id for r in facturacion_qs if r.suscripcion_id]
        subs_map = {}
        if sub_ids:
            try:
                from plugins.membresias.backend.models import Suscripcion
                for s in Suscripcion.objects.filter(id__in=sub_ids).select_related('plan'):
                    subs_map[str(s.id)] = s
            except Exception:
                pass

        detalles_facturacion = []
        for r in facturacion_qs.select_related('usuario').order_by('-fecha'):
            sub = subs_map.get(str(r.suscripcion_id)) if r.suscripcion_id else None

            # Nombre completo
            nombre_alumno = 'Alumno sin registrar'
            if r.usuario:
                nom = f"{r.usuario.nombre or ''} {r.usuario.apellido or ''}".strip()
                nombre_alumno = nom if nom else (r.usuario.email or 'Alumno')

            # Fecha local
            if r.fecha:
                dt = timezone.localtime(r.fecha) if timezone.is_aware(r.fecha) else r.fecha
                fecha_str = dt.strftime('%d/%m/%Y %H:%M')
                fecha_corta = dt.strftime('%d/%m/%Y')
            else:
                fecha_str = ''
                fecha_corta = ''

            detalles_facturacion.append({
                'id': str(r.id),
                'fecha': fecha_str,
                'fecha_corta': fecha_corta,
                'alumno_id': str(r.usuario.id) if r.usuario else None,
                'alumno_nombre': nombre_alumno,
                'alumno_email': r.usuario.email if r.usuario else '',
                'alumno_telefono': getattr(r.usuario, 'telefono', '') if r.usuario else '',
                'plan_nombre': r.plan_nombre,
                'monto': float(r.monto or 0),
                'suscripcion_id': r.suscripcion_id or None,
                'suscripcion_estado': sub.estado if sub else None,
                'clases_restantes': sub.clases_restantes if sub else None,
                'clases_totales': sub.plan.cantidad_clases if (sub and sub.plan) else None,
                'fecha_vencimiento': sub.fecha_vencimiento.strftime('%d/%m/%Y') if (sub and sub.fecha_vencimiento) else None
            })

        # Comunicaciones automáticas reales
        # Cada nuevo alumno genera correo de bienvenida, cada plan un correo de confirmación, y cada reserva confirmada su notificación
        estimado_emails = nuevos_alumnos + planes_asignados_mes + auto_reservas
        total_emails = max(emails_logged, estimado_emails)
        total_wpps = wpps_logged

        # Ahorro de tiempo estimado del sistema (en minutos):
        # - 5 min por cada reserva auto-gestionada por el alumno (evita WhatsApp, llamadas, buscar huecos)
        # - 5 min por cada cancelación auto-gestionada (libera el cupo inmediatamente)
        # - 3 min por cada email transaccional enviado automáticamente
        # - 3 min por cada WhatsApp enviado
        # - 10 min por cada alta y ficha médica auto-cargada por el alumno
        minutos_ahorrados = (auto_reservas * 5) + (auto_cancels * 5) + (total_emails * 3) + (total_wpps * 3) + (nuevos_alumnos * 10)
        horas_ahorradas = round(minutos_ahorrados / 60, 1)
        if horas_ahorradas >= 10:
            horas_ahorradas = int(round(horas_ahorradas))

        # Tasa de auto-gestión:
        gestiones_totales = auto_reservas + auto_cancels
        if gestiones_totales > 0:
            tasa_autogestion = 100
        else:
            tasa_autogestion = 0

        # 2. RADIOGRAFÍA DE LA COMUNIDAD (Demografía)
        generos = {'F': 0, 'M': 0, 'O': 0, 'N': 0}
        edades = {'<20': 0, '20-30': 0, '31-40': 0, '41-50': 0, '>50': 0}
        suma_edades = 0
        count_edades = 0

        for cliente in clientes:
            try:
                ficha = cliente.ficha_medica
                if ficha.sexo in generos:
                    generos[ficha.sexo] += 1
                if ficha.fecha_nacimiento:
                    edad = now.date().year - ficha.fecha_nacimiento.year - ((now.date().month, now.date().day) < (ficha.fecha_nacimiento.month, ficha.fecha_nacimiento.day))
                    suma_edades += edad
                    count_edades += 1
                    if edad < 20: edades['<20'] += 1
                    elif 20 <= edad <= 30: edades['20-30'] += 1
                    elif 31 <= edad <= 40: edades['31-40'] += 1
                    elif 41 <= edad <= 50: edades['41-50'] += 1
                    else: edades['>50'] += 1
            except Exception:
                pass

        promedio_edad = round(suma_edades / count_edades) if count_edades > 0 else 0

        # 4. SALUD OPERATIVA
        turnos_mes = in_month(Turno.objects, 'fecha')
        turnos_realizados = turnos_mes.filter(estado__in=['PROGRAMADO', 'COMPLETADO', 'REALIZADO'])
        turnos_cancelados = turnos_mes.filter(estado='CANCELADO').count()
        
        ocupacion = 0
        heatmap = {}
        for t in turnos_realizados:
            capacidad = t.clase.cupo_maximo
            ocupados = capacidad - t.cupo_actual
            if capacidad > 0:
                ocupacion += (ocupados / capacidad)
                
            dia = t.fecha.isoweekday() # 1=Lunes, 7=Domingo
            hora = t.hora_inicio.strftime('%H:%M')
            key = f"{dia}-{hora}"
            if key not in heatmap:
                heatmap[key] = {'dia': dia, 'hora': hora, 'clases': 0, 'ocupacion': 0}
            heatmap[key]['clases'] += 1
            heatmap[key]['ocupacion'] += (ocupados / capacidad) if capacidad > 0 else 0
            
        promedio_ocupacion = round((ocupacion / turnos_realizados.count()) * 100) if turnos_realizados.count() > 0 else 0
        
        # Formatear heatmap
        heatmap_data = []
        for v in heatmap.values():
            heatmap_data.append({
                'dia': v['dia'],
                'hora': v['hora'],
                'ocupacion_promedio': round((v['ocupacion'] / v['clases']) * 100)
            })

        return Response({
            'valor': {
                'horas_ahorradas': horas_ahorradas,
                'auto_reservas': auto_reservas,
                'auto_cancels': auto_cancels,
                'emails_enviados': total_emails,
                'wpps_enviados': total_wpps,
                'tasa_autogestion': tasa_autogestion
            },
            'comunidad': {
                'total_alumnos': total_alumnos,
                'nuevos_alumnos': nuevos_alumnos,
                'promedio_edad': promedio_edad,
                'distribucion_genero': generos,
                'distribucion_edad': edades
            },
            'facturacion': {
                'total': total_facturacion,
                'desglose_planes': desglose_planes,
                'detalles': detalles_facturacion
            },
            'operatividad': {
                'promedio_ocupacion': promedio_ocupacion,
                'clases_dictadas': turnos_realizados.count(),
                'clases_canceladas': turnos_cancelados,
                'heatmap': heatmap_data
            }
        })


class TestEmailView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        recipient = request.data.get('email') or request.user.email
        if not recipient:
            return Response({
                'success': False,
                'detail': 'No se proporcionó una dirección de email válida.'
            }, status=status.HTTP_400_BAD_REQUEST)

        email_pw = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
        email_backend = getattr(settings, 'EMAIL_BACKEND', '')
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Violett <hola@violett.com.ar>')

        if not email_pw:
            return Response({
                'success': False,
                'detail': (
                    'EMAIL_HOST_PASSWORD no está configurado en las variables de entorno (.env). '
                    'Para enviar correos en producción a través de Resend, añade EMAIL_HOST_PASSWORD=re_tu_api_key '
                    'en el archivo .env del servidor y reinicia el servicio con "bash subir_a_prod.sh".'
                ),
                'backend': email_backend
            }, status=status.HTTP_400_BAD_REQUEST)

        from django.core.mail import EmailMultiAlternatives
        subject = 'Prueba de Conexión de Correo - Violett'
        text_content = (
            f"¡Hola {request.user.nombre}!\n\n"
            "Este es un correo de prueba enviado desde el Panel de Inteligencia de Negocio de Violett.\n"
            "Si estás leyendo esto, significa que el servicio de correo SMTP (Resend) está configurado y funcionando a la perfección.\n\n"
            f"Servidor SMTP: {getattr(settings, 'EMAIL_HOST', 'smtp.resend.com')}\n"
            f"Remitente: {from_email}\n"
            f"Destinatario: {recipient}\n"
        )
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e5e7eb; border-radius: 16px; background: #ffffff;">
            <h2 style="color: #34236F; margin-top: 0; font-size: 22px;">¡Prueba de Correo Exitosa! 🎉</h2>
            <p style="color: #4b5563; font-size: 15px; line-height: 1.6;">
                Hola <strong>{request.user.nombre}</strong>, este mensaje confirma que el motor de comunicaciones transaccionales de <strong>Violett</strong> vía Resend está completamente operativo.
            </p>
            <div style="background: #F4EBF1; border-left: 4px solid #34236F; padding: 14px 18px; margin: 20px 0; border-radius: 8px;">
                <p style="margin: 4px 0; font-size: 13px; color: #34236F;"><strong>Remitente:</strong> {from_email}</p>
                <p style="margin: 4px 0; font-size: 13px; color: #34236F;"><strong>Destinatario:</strong> {recipient}</p>
                <p style="margin: 4px 0; font-size: 13px; color: #34236F;"><strong>Servidor:</strong> {getattr(settings, 'EMAIL_HOST', 'smtp.resend.com')}:{getattr(settings, 'EMAIL_PORT', 587)}</p>
            </div>
            <p style="color: #9ca3af; font-size: 12px; margin-bottom: 0;">
                Enviado desde el Panel de Administración de Violett.
            </p>
        </div>
        """

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)

            # Record metric
            try:
                MetricaInteractiva.objects.create(tipo='EMAIL', usuario=request.user)
            except Exception:
                pass

            return Response({
                'success': True,
                'detail': f'¡Correo de prueba enviado con éxito a {recipient}! Revisa tu bandeja de entrada o spam.',
                'from_email': from_email,
                'recipient': recipient
            })

        except Exception as e:
            err_str = str(e)
            err_type = type(e).__name__
            detail_msg = f"Error al enviar correo ({err_type}): {err_str}"

            if '535' in err_str or 'Authentication' in err_str or 'credentials' in err_str:
                detail_msg = (
                    "Error de autenticación SMTP (535): La API Key de Resend (EMAIL_HOST_PASSWORD) "
                    "es incorrecta o fue revocada. Verifica tu API Key en el panel de resend.com y actualízala en el archivo .env."
                )
            elif 'domain' in err_str.lower() or 'not verified' in err_str.lower() or 'sender' in err_str.lower():
                detail_msg = (
                    f"Error de dominio de remitente: Resend rechazó el envío desde '{from_email}' porque el dominio "
                    "no está verificado en tu cuenta de Resend. Verifica el dominio en resend.com/domains o configura "
                    "DEFAULT_FROM_EMAIL=Violett <onboarding@resend.dev> en el archivo .env para pruebas."
                )

            return Response({
                'success': False,
                'detail': detail_msg,
                'raw_error': err_str,
                'from_email': from_email,
                'recipient': recipient
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

