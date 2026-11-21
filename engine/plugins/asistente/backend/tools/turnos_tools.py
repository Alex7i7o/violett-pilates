import datetime
import logging
from typing import Optional, List, Dict
from django.utils import timezone
from django.db import transaction
from langchain_core.tools import tool

from core.models import Turno, Reserva, Usuario
from ..config_loader import get_asistente_config
from .profesores_tools import resolver_fecha, resolver_hora, obtener_profesor_de_turno

logger = logging.getLogger(__name__)

@tool
def consultar_turnos_disponibles(fecha_str: str) -> str:
    """
    Consulta los turnos disponibles de Pilates Reformer para una fecha específica ('hoy', 'mañana', 'lunes', '2026-10-23', etc.).
    Retorna la lista de horarios con cupos libres (máximo 3 camillas por turno).
    NUNCA expongas IDs numéricos al usuario final.
    """
    target_date = resolver_fecha(fecha_str)

    # Aseguramos generación desde plantillas únicamente si aún no hay turnos generados para esa fecha
    if not Turno.objects.filter(fecha=target_date).exists():
        try:
            from core.services import generar_turnos_desde_plantillas
            generar_turnos_desde_plantillas()
        except Exception as e:
            logger.warning(f"Error generando turnos: {e}")

    turnos = Turno.objects.filter(
        fecha=target_date,
        estado='PROGRAMADO',
        cupo_actual__gt=0
    ).select_related('clase').order_by('hora_inicio')

    if not turnos.exists():
        return f"No hay turnos con camillas disponibles para el {target_date.strftime('%d/%m/%Y')}."

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nombre = dias_semana[target_date.weekday()]

    resultado = [f"✦ Turnos disponibles para el {dia_nombre} {target_date.strftime('%d/%m')}:"]
    turnos_visibles_count = 0
    for t in turnos:
        prof_obj = obtener_profesor_de_turno(t)
        # Ocultar clases que no tengan profesor confirmado a las alumnas
        if not prof_obj or not getattr(prof_obj, 'is_active', True):
            continue
        profe = f" (Profe: {prof_obj.nombre})" if prof_obj and hasattr(prof_obj, 'nombre') else ""
        camillas_libres = t.cupo_actual
        resultado.append(
            f"• {t.hora_inicio.strftime('%H:%M')} hs - {t.clase.nombre}{profe} "
            f"({camillas_libres} camilla{'s' if camillas_libres > 1 else ''} libre{'s' if camillas_libres > 1 else ''})"
        )
        turnos_visibles_count += 1

    if turnos_visibles_count == 0:
        return f"No hay turnos con profesor confirmado disponibles para el {dia_nombre} {target_date.strftime('%d/%m')}."

    return "\n".join(resultado)


@tool
def reservar_camilla_turno(usuario_id: str, fecha_o_dia: str = "", hora_str: str = "", turno_id: str = "") -> str:
    """
    Reserva 1 camilla de Reformer para una alumna.
    Podés especificar 'turno_id' O 'fecha_o_dia' (ej: 'hoy', 'mañana', 'viernes') junto a 'hora_str' (ej: '18:00').
    Valida atómicamente el cupo disponible (máximo 3 camillas) y descuenta 1 crédito de su plan activo.
    """
    if not usuario_id:
        return "No estás identificada aún en el sistema para realizar la reserva."

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return "No se encontró el perfil de la alumna en el sistema."

    try:
        from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
    except ImportError:
        Suscripcion = None
        ReservaMembresia = None

    # 1. Buscar turno destino solicitado primero
    turno = None
    if turno_id:
        try:
            turno = Turno.objects.filter(id=turno_id).first()
        except Exception:
            turno = None

    if not turno and fecha_o_dia:
        target_date = resolver_fecha(fecha_o_dia)
        target_time = resolver_hora(hora_str) if hora_str else None
        qs = Turno.objects.filter(fecha=target_date, estado='PROGRAMADO')
        if target_time:
            qs = qs.filter(hora_inicio__hour=target_time.hour, hora_inicio__minute=target_time.minute)
        turno = qs.first()

    if not turno:
        return f"No se encontró ningún turno programado para {fecha_o_dia} a las {hora_str} hs."

    # Validar que la clase tenga profesor asignado
    prof_obj = obtener_profesor_de_turno(turno)
    if not prof_obj or not getattr(prof_obj, 'is_active', True):
        return f"Ese horario ({turno.hora_inicio.strftime('%H:%M')} hs) aún no tiene profesor asignado confirmado, por lo que no está disponible para reservar. Por favor elegí otro de los horarios con profe confirmado."

    # 2. Validar suscripción activa y créditos
    suscripcion = None
    if Suscripcion:
        suscripcion = Suscripcion.objects.filter(
            usuario=usuario,
            estado__in=['ACTIVO', 'AGOTADO'],
            fecha_vencimiento__gte=timezone.localdate()
        ).order_by('-fecha_inicio').first()

        if not suscripcion or suscripcion.clases_restantes <= 0:
            today = timezone.localdate()
            now_time = timezone.localtime().time()
            futuras = list(Reserva.objects.filter(
                usuario=usuario,
                estado='CONFIRMADA',
                turno__fecha__gte=today
            ).exclude(
                turno__fecha=today,
                turno__hora_inicio__lt=now_time
            ).select_related('turno', 'turno__clase').order_by('turno__fecha', 'turno__hora_inicio'))

            if futuras:
                dias_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
                lista_futuras = []
                for r in futuras:
                    t_item = r.turno
                    dia_nom = dias_es[t_item.fecha.weekday()]
                    p = obtener_profesor_de_turno(t_item)
                    profe_str = f" - Profe: {p.nombre}" if p and hasattr(p, 'nombre') else ""
                    lista_futuras.append(f"  • {dia_nom} {t_item.fecha.strftime('%d/%m')} a las {t_item.hora_inicio.strftime('%H:%M')} hs ({t_item.clase.nombre}{profe_str})")
                
                str_futuras = "\n".join(lista_futuras)
                t_dia = dias_es[turno.fecha.weekday()]
                target_str = f"*{t_dia} {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs*"

                conv = get_conversacion_activa()
                if conv:
                    if not isinstance(conv.metadata, dict):
                        conv.metadata = {}
                    conv.metadata['reprogramacion_pendiente_destino_turno_id'] = str(turno.id)
                    conv.metadata['reprogramacion_pendiente_destino_fecha'] = turno.fecha.strftime('%Y-%m-%d')
                    conv.metadata['reprogramacion_pendiente_destino_hora'] = turno.hora_inicio.strftime('%H:%M')
                    conv.save(update_fields=['metadata'])

                return f"""✦ No te quedan créditos libres en tu abono en este momento, pero tenés estas clases ya agendadas a futuro:
{str_futuras}

¿Querés que cambiemos alguna de estas clases para pasarla al nuevo horario de {target_str}?
Decime cuál te gustaría mover (por ejemplo: "Cambiame la del {dias_es[futuras[0].turno.fecha.weekday()]}" o "Pasá la del {futuras[0].turno.fecha.strftime('%d/%m')}") y te la paso directo ✨."""

            return "No tenés créditos disponibles en tu plan actual para agendar esta clase. ¿Querés que te pase las opciones para renovar tu abono?"

    # Transacción atómica con lock para prevenir sobreventa de la 3era camilla
    with transaction.atomic():
        t_locked = Turno.objects.select_for_update().get(id=turno.id)

        if t_locked.cupo_actual <= 0:
            return f"Disculpá, justo se acaba de completar la última camilla libre de las {t_locked.hora_inicio.strftime('%H:%M')} hs."

        # Verificar si ya tiene reserva en este turno
        existing = Reserva.objects.filter(turno=t_locked, usuario=usuario).first()
        if existing:
            if existing.estado == 'CONFIRMADA':
                return f"Ya tenés una reserva confirmada para este turno de las {t_locked.hora_inicio.strftime('%H:%M')} hs."
            existing.estado = 'CONFIRMADA'
            existing.save()
            res = existing
        else:
            res = Reserva.objects.create(
                turno=t_locked,
                usuario=usuario,
                estado='CONFIRMADA'
            )

        # Descontar cupo
        t_locked.cupo_actual -= 1
        t_locked.save()

        # Descontar crédito
        if suscripcion and ReservaMembresia:
            ReservaMembresia.objects.get_or_create(reserva=res, defaults={'suscripcion': suscripcion})
            suscripcion.clases_restantes -= 1
            if suscripcion.clases_restantes == 0:
                suscripcion.estado = 'AGOTADO'
            suscripcion.save()

        # Disparar hooks
        from backend_core.hooks import registry
        registry.execute('reserva_creada', res)

    creditos_rest = f" Te quedan {suscripcion.clases_restantes} clases disponibles." if suscripcion else ""
    return f"✦ ¡Listo! Quedó confirmada tu camilla para el {t_locked.fecha.strftime('%d/%m')} a las {t_locked.hora_inicio.strftime('%H:%M')} hs en {t_locked.clase.nombre}.{creditos_rest}"


@tool
def consultar_mis_reservas_alumna(usuario_id: str = "") -> str:
    """
    Retorna la lista de clases agendadas y horario fijo que tiene una alumna en el estudio.
    Muestra los turnos prolijamente ordenados por fecha y hora con la profesora a cargo, sin IDs internos.
    """
    from core.models import Turno, Reserva, Usuario
    usuario = None
    if usuario_id:
        try:
            usuario = Usuario.objects.filter(id=usuario_id).first()
        except Exception:
            usuario = None

    if not usuario:
        from .gestion_tools import get_conversacion_activa, buscar_usuario_por_telefono, get_ultima_alumna_activa
        conv = get_conversacion_activa()
        if conv:
            if conv.usuario:
                usuario = conv.usuario
            elif conv.telefono:
                usuario = buscar_usuario_por_telefono(conv.telefono)
        if not usuario:
            usuario = get_ultima_alumna_activa()

    if not usuario:
        return "No estás identificada aún en el sistema como alumna de Violett Pilates ✦."

    today = timezone.localdate()
    now_time = timezone.localtime().time()

    reservas = Reserva.objects.filter(
        usuario=usuario,
        estado='CONFIRMADA',
        turno__fecha__gte=today
    ).select_related('turno', 'turno__clase').order_by('turno__fecha', 'turno__hora_inicio')

    # Excluir turnos de hoy que ya terminaron
    reservas_futuras = [
        r for r in reservas
        if not (r.turno.fecha == today and r.turno.hora_fin and r.turno.hora_fin <= now_time)
    ]

    # Consultar esquemas fijos recurrentes
    horarios_fijos = []
    try:
        from plugins.recurrencias.backend.models import Recurrencia
        recs = Recurrencia.objects.filter(usuario=usuario, is_active=True).select_related('clase')
        dias_es = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 4: 'Jueves', 5: 'Viernes', 6: 'Sábado', 7: 'Domingo'}
        for rec in recs:
            d_nom = dias_es.get(rec.dia_semana, f"Día {rec.dia_semana}")
            h_str = rec.hora_inicio.strftime('%H:%M')
            horarios_fijos.append(f"• Todos los *{d_nom}s a las {h_str} hs* ({rec.clase.nombre})")
    except Exception:
        pass

    dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    nombre_display = usuario.nombre.split()[0] if usuario.nombre else ""
    saludo = f"¡Hola {nombre_display}! ✦ " if nombre_display else "✦ "

    from core.services import actualizar_reservas_pasadas_a_tomadas
    actualizar_reservas_pasadas_a_tomadas(usuario=usuario)

    asistidas_recientes = list(Reserva.objects.filter(
        usuario=usuario,
        estado='TOMADA'
    ).select_related('turno', 'turno__clase').order_by('-turno__fecha', '-turno__hora_inicio')[:3])

    if not reservas_futuras and not horarios_fijos:
        creditos_info = ""
        try:
            from plugins.membresias.backend.models import Suscripcion
            sub = Suscripcion.objects.filter(usuario=usuario, estado__in=['ACTIVO', 'AGOTADO']).first()
            if sub and sub.clases_restantes > 0:
                creditos_info = f"\n\nTenés *{sub.clases_restantes} clase(s) disponibles* en tu {sub.plan.nombre}. ¿Querés que te busque lugar en algún día y horario para agendarte?"
            elif sub and sub.clases_restantes == 0:
                creditos_info = f"\n\nTu {sub.plan.nombre} no tiene créditos libres en este momento. Si querés sumar una clase individual o renovar, avisame con gusto 🌸."
        except Exception:
            pass

        msg_base = f"{saludo}Actualmente no tenés ninguna clase agendada a futuro en Violett Pilates."
        if asistidas_recientes:
            msg_base += "\n\n✦ *Tus últimas clases asistidas:*"
            for r in asistidas_recientes:
                t = r.turno
                dia_nombre = dias_semana[t.fecha.weekday()]
                prof_obj = obtener_profesor_de_turno(t)
                profe_txt = f" (Profe: {prof_obj.nombre})" if prof_obj and hasattr(prof_obj, 'nombre') else ""
                msg_base += f"\n• *{dia_nombre} {t.fecha.strftime('%d/%m')} a las {t.hora_inicio.strftime('%H:%M')} hs* - {t.clase.nombre}{profe_txt}"

        return f"{msg_base}{creditos_info}"

    resultado = [f"{saludo}Tus próximas clases agendadas en Violett Pilates:"]
    for r in reservas_futuras:
        t = r.turno
        dia_nombre = dias_semana[t.fecha.weekday()]
        prof_obj = obtener_profesor_de_turno(t)
        profe_txt = f" (Profe: {prof_obj.nombre})" if prof_obj and hasattr(prof_obj, 'nombre') else ""
        tipo = " *(Horario fijo)*" if getattr(r, 'es_recurrente', False) else ""
        resultado.append(
            f"• *{dia_nombre} {t.fecha.strftime('%d/%m')} a las {t.hora_inicio.strftime('%H:%M')} hs* - {t.clase.nombre}{profe_txt}{tipo}"
        )

    if horarios_fijos and not any(r.es_recurrente for r in reservas_futuras):
        resultado.append("\n✦ *Tu esquema de horario fijo semanal:*")
        resultado.extend(horarios_fijos)

    if asistidas_recientes:
        resultado.append("\n✦ *Tus últimas clases asistidas:*")
        for r in asistidas_recientes:
            t = r.turno
            dia_nombre = dias_semana[t.fecha.weekday()]
            prof_obj = obtener_profesor_de_turno(t)
            profe_txt = f" (Profe: {prof_obj.nombre})" if prof_obj and hasattr(prof_obj, 'nombre') else ""
            resultado.append(f"• *{dia_nombre} {t.fecha.strftime('%d/%m')} a las {t.hora_inicio.strftime('%H:%M')} hs* - {t.clase.nombre}{profe_txt}")

    return "\n".join(resultado)


@tool
def cancelar_reserva_alumna(usuario_id: str, fecha_o_dia: str, hora_str: str = "") -> str:
    """
    Cancela una reserva de clase de una alumna, aplicando la regla de negocio estricta de 24 horas:
    - Con MÁS de 24 hs de anticipación: Cancela la reserva, libera la camilla y RECUPERA el crédito a su abono.
    - Con MENOS de 24 hs de anticipación: Cancela la reserva y libera la camilla, pero la alumna PIERDE el crédito de la clase (política del estudio).
    Parámetros:
    - usuario_id: ID del usuario
    - fecha_o_dia: 'hoy', 'mañana', 'lunes', '2026-10-23'
    - hora_str: '18:00', '10:30', etc.
    """
    if not usuario_id:
        return "No estás identificada aún en el sistema."

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return "No se encontró el perfil de la alumna."

    target_date = resolver_fecha(fecha_o_dia)
    target_time = resolver_hora(hora_str) if hora_str else None

    qs = Reserva.objects.filter(
        usuario=usuario,
        estado='CONFIRMADA',
        turno__fecha=target_date
    ).select_related('turno', 'turno__clase')

    if target_time:
        qs = qs.filter(turno__hora_inicio__hour=target_time.hour, turno__hora_inicio__minute=target_time.minute)

    reserva = qs.first()
    if not reserva:
        hora_txt = f" a las {hora_str} hs" if hora_str else ""
        return f"No tenés ninguna reserva confirmada para el {target_date.strftime('%d/%m')}{hora_txt}."

    turno = reserva.turno

    # Cálculo exacto de horas de anticipación
    ahora = timezone.localtime()
    tz = ahora.tzinfo
    clase_dt = datetime.datetime.combine(turno.fecha, turno.hora_inicio)
    if timezone.is_naive(clase_dt):
        clase_dt = timezone.make_aware(clase_dt, tz)

    horas_anticipacion = (clase_dt - ahora).total_seconds() / 3600.0

    # Buscar suscripción vinculada
    try:
        from plugins.membresias.backend.models import Suscripcion, ReservaMembresia
        res_mem = ReservaMembresia.objects.filter(reserva=reserva).first()
        suscripcion = res_mem.suscripcion if res_mem else None
        if not suscripcion:
            suscripcion = Suscripcion.objects.filter(
                usuario=usuario,
                estado__in=['ACTIVO', 'AGOTADO']
            ).order_by('-fecha_inicio').first()
    except ImportError:
        suscripcion = None

    with transaction.atomic():
        t_locked = Turno.objects.select_for_update().get(id=turno.id)

        # Aplicar regla de 24 horas
        if horas_anticipacion >= 24.0:
            reserva.estado = 'CANCELADA_TIEMPO'
            recupero_credito = True
        else:
            reserva.estado = 'CANCELADA_TARDIA'
            recupero_credito = False

        reserva.save()

        # Liberar cupo de camilla
        max_cupo = turno.clase.cupo_maximo if turno.clase else 3
        t_locked.cupo_actual = min(max_cupo, t_locked.cupo_actual + 1)
        t_locked.save()

        from backend_core.hooks import registry
        hook_name = 'reserva_cancelada_a_tiempo' if recupero_credito else 'reserva_cancelada_tardia'
        try:
            registry.execute(hook_name, reserva)
        except Exception as e:
            logger.warning(f"Error hook {hook_name}: {e}")
        try:
            registry.execute('reserva_cancelada', reserva)
        except Exception:
            pass

        # Fallback si no había ReservaMembresia vinculada pero hay suscripción
        if recupero_credito and suscripcion and not res_mem:
            suscripcion.clases_restantes += 1
            if suscripcion.estado == 'AGOTADO':
                suscripcion.estado = 'ACTIVO'
            suscripcion.save()
        elif suscripcion:
            suscripcion.refresh_from_db()

    if recupero_credito:
        creditos_rest = f" Tu saldo actual es de {suscripcion.clases_restantes} clases disponibles." if suscripcion else ""
        return (
            f"✦ Tu clase del {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs ha sido cancelada con éxito. "
            f"Como cancelaste con más de 24 hs de anticipación, recuperaste tu crédito para volver a agendar en cualquier momento del mes.{creditos_rest}"
        )
    else:
        return (
            f"✦ Tu clase del {turno.fecha.strftime('%d/%m')} a las {turno.hora_inicio.strftime('%H:%M')} hs ha sido cancelada y la camilla quedó liberada. "
            f"Tené en cuenta que, según la política oficial del estudio (cancelación con menos de 24 hs de anticipación), "
            f"el crédito de la clase no se recupera ✦."
        )


@tool
def reprogramar_reserva_alumna(usuario_id: str = "", fecha_origen: str = "", hora_origen: str = "", fecha_destino: str = "", hora_destino: str = "") -> str:
    """
    Permite a la alumna mover o reprogramar una clase que ya tiene agendada hacia un nuevo horario disponible,
    sin consumir créditos adicionales ni costo extra (intercambio directo 1 a 1).
    Especialmente útil cuando no tiene créditos libres pero sí clases agendadas y desea cambiarse de horario.
    Parámetros:
      - usuario_id: ID de la alumna.
      - fecha_origen: Día o fecha de la clase que desea cambiar (ej: 'miércoles', '18/11', 'hoy').
      - hora_origen: Opcional. Hora de la clase origen (ej: '19:00', '18hs').
      - fecha_destino: Día o fecha del nuevo horario que desea tomar. Si se omite, se usa el turno consultado previamente.
      - hora_destino: Hora del nuevo turno (ej: '18:00', '19hs'). Si se omite, se usa el turno consultado previamente.
    """
    usuario = None
    if usuario_id:
        try:
            usuario = Usuario.objects.filter(id=usuario_id).first()
        except Exception:
            usuario = None

    conv = get_conversacion_activa()
    if not usuario and conv:
        if conv.usuario:
            usuario = conv.usuario
        elif conv.telefono:
            usuario = buscar_usuario_por_telefono(conv.telefono)
        if not usuario:
            usuario = get_ultima_alumna_activa()

    if not usuario:
        return "No estás identificada en el sistema para realizar la reprogramación."

    today = timezone.localdate()
    now_time = timezone.localtime().time()

    # 1. Buscar turno de destino
    turno_destino = None
    meta = (conv.metadata or {}) if conv else {}
    if fecha_destino:
        t_dest_date = resolver_fecha(fecha_destino)
        t_dest_time = resolver_hora(hora_destino) if hora_destino else None
        qs_dest = Turno.objects.filter(fecha=t_dest_date, estado='PROGRAMADO')
        if t_dest_time:
            qs_dest = qs_dest.filter(hora_inicio__hour=t_dest_time.hour, hora_inicio__minute=t_dest_time.minute)
        turno_destino = qs_dest.first()
    elif meta.get('reprogramacion_pendiente_destino_turno_id'):
        turno_destino = Turno.objects.filter(id=meta.get('reprogramacion_pendiente_destino_turno_id'), estado='PROGRAMADO').first()

    if not turno_destino:
        return "No pude identificar con certeza a qué nuevo horario querés mover la clase. Por favor indicame el día y horario al que te querés anotar (por ejemplo: 'el viernes a las 18 hs')."

    # Validar que el turno destino tenga profesor confirmado
    prof_dest = obtener_profesor_de_turno(turno_destino)
    if not prof_dest or not getattr(prof_dest, 'is_active', True):
        return f"El turno de las {turno_destino.hora_inicio.strftime('%H:%M')} hs aún no tiene profesor asignado confirmado, por lo que no está disponible para reprogramar. Por favor elegí otro de los horarios disponibles."

    # 2. Buscar turno de origen de la alumna
    reservas_futuras = list(Reserva.objects.filter(
        usuario=usuario,
        estado='CONFIRMADA',
        turno__fecha__gte=today
    ).exclude(
        turno__fecha=today,
        turno__hora_inicio__lt=now_time
    ).exclude(
        turno=turno_destino
    ).select_related('turno', 'turno__clase').order_by('turno__fecha', 'turno__hora_inicio'))

    if not reservas_futuras:
        return "No tenés ninguna clase agendada a futuro que puedas cambiar."

    reserva_elegida = None
    if fecha_origen:
        f_orig_date = resolver_fecha(fecha_origen)
        h_orig_time = resolver_hora(hora_origen) if hora_origen else None
        for r in reservas_futuras:
            if r.turno.fecha == f_orig_date:
                if h_orig_time:
                    if r.turno.hora_inicio.hour == h_orig_time.hour:
                        reserva_elegida = r
                        break
                else:
                    reserva_elegida = r
                    break

    # Si no especificó fecha origen o no hizo match exacto, pero solo tiene 1 reserva futura, elegir esa
    if not reserva_elegida:
        if len(reservas_futuras) == 1:
            reserva_elegida = reservas_futuras[0]
        else:
            dias_es = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']
            lista = [f"• {dias_es[r.turno.fecha.weekday()]} {r.turno.fecha.strftime('%d/%m')} a las {r.turno.hora_inicio.strftime('%H:%M')} hs" for r in reservas_futuras]
            return f"Tenés varias clases agendadas. ¿Cuál de estas querés cambiar por el turno de las {turno_destino.hora_inicio.strftime('%H:%M')} hs?\n" + "\n".join(lista)

    from core.services import reprogramar_reserva
    exito, mensaje = reprogramar_reserva(
        usuario=usuario,
        turno_origen_id=str(reserva_elegida.turno.id),
        turno_destino_id=str(turno_destino.id)
    )

    if not exito:
        return f"No se pudo reprogramar la clase: {mensaje}"

    # Limpiar metadata de reprogramación pendiente
    if conv and conv.metadata:
        conv.metadata.pop('reprogramacion_pendiente_destino_turno_id', None)
        conv.metadata.pop('reprogramacion_pendiente_destino_fecha', None)
        conv.metadata.pop('reprogramacion_pendiente_destino_hora', None)
        conv.save(update_fields=['metadata'])

    dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_orig = dias_es[reserva_elegida.turno.fecha.weekday()]
    dia_dest = dias_es[turno_destino.fecha.weekday()]
    p_dest = obtener_profesor_de_turno(turno_destino)
    profe_txt = f" (con la profe {p_dest.nombre})" if p_dest and hasattr(p_dest, 'nombre') else ""

    nombre_display = usuario.nombre.split()[0] if usuario.nombre else ""
    saludo = f"¡Listo {nombre_display}! ✦ " if nombre_display else "✦ "

    return f"""{saludo}Moví tu clase del *{dia_orig} {reserva_elegida.turno.fecha.strftime('%d/%m')} de las {reserva_elegida.turno.hora_inicio.strftime('%H:%M')} hs* al nuevo horario del *{dia_dest} {turno_destino.fecha.strftime('%d/%m')} a las {turno_destino.hora_inicio.strftime('%H:%M')} hs*{profe_txt}.

¡Ya quedó asegurado tu lugar en la camilla! ✨"""


@tool
def registrar_prospecto_o_clase_prueba(nombre_completo: str, fecha_o_dia: str, hora_str: str, telefono: str = "") -> str:
    """
    Registra y aparta una camilla de clase de prueba o primera clase para una persona interesada / prospecto nuevo que aún no tiene cuenta ni abono en la app.
    Aparta la camilla en el turno correspondiente (máximo 3 camillas) y notifica a la dueña (Deby) por WhatsApp para el seguimiento comercial.

    Parámetros:
    - nombre_completo: Nombre y apellido de la persona (ej: 'Camila Gómez', 'Lucía').
    - fecha_o_dia: 'hoy', 'mañana' o día/fecha deseada (ej: 'lunes', '24/11', 'mañana').
    - hora_str: Hora deseada (ej: '10:00', '18:00', '19', '18:30').
    - telefono: Teléfono de la interesada (opcional; si no se indica se extrae de la conversación activa).
    """
    target_date = resolver_fecha(fecha_o_dia)
    target_time = resolver_hora(hora_str) if hora_str else None

    qs = Turno.objects.filter(fecha=target_date, estado='PROGRAMADO').select_related('clase')
    if target_time:
        qs = qs.filter(hora_inicio__hour=target_time.hour, hora_inicio__minute=target_time.minute)

    turno = qs.first()
    dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias_es[target_date.weekday()]

    if not turno:
        turnos_dia = Turno.objects.filter(fecha=target_date, estado='PROGRAMADO', cupo_actual__gt=0).select_related('clase').order_by('hora_inicio')
        if turnos_dia.exists():
            lista_horarios = []
            for t_item in turnos_dia:
                p_item = obtener_profesor_de_turno(t_item)
                p_str = f" (Profe: {p_item.nombre})" if p_item and hasattr(p_item, 'nombre') else ""
                lista_horarios.append(f"• {t_item.hora_inicio.strftime('%H:%M')} hs: {t_item.cupo_actual} camilla(s) libre(s){p_str}")
            return f"✦ No encontré una clase programada exactamente a las {hora_str} hs para el {dia_nom} {target_date.strftime('%d/%m')}.\n\nLos horarios con camillas disponibles para ese día son:\n" + "\n".join(lista_horarios) + f"\n\n¿En cuál de estos te gustaría reservar tu camilla?"
        else:
            return f"✦ No hay turnos disponibles para el {dia_nom} {target_date.strftime('%d/%m/%Y')} en ese horario."

    from .gestion_tools import get_conversacion_activa
    conv = get_conversacion_activa()
    tel_clean = telefono.replace('+', '').replace(' ', '').replace('-', '') if telefono else (conv.telefono if conv else "")

    nom_limpio = nombre_completo.strip()
    nombre_pila = nom_limpio.split()[0] if nom_limpio else "Visitante"

    fecha_fmt = turno.fecha.strftime('%d/%m')
    hora_clean = turno.hora_inicio.strftime('%H:%M')
    prof_obj = obtener_profesor_de_turno(turno)
    profe_str = f" con la profe {prof_obj.nombre}" if prof_obj and hasattr(prof_obj, 'nombre') else ""

    with transaction.atomic():
        t_locked = Turno.objects.select_for_update().get(id=turno.id)
        if t_locked.cupo_actual <= 0:
            return f"✦ Disculpá {nombre_pila}, justo se acaba de ocupar la última camilla libre de las {hora_clean} hs del {dia_nom} {fecha_fmt}. ¿Querés que miremos otro horario para tu clase de prueba?"

        res = Reserva.objects.create(
            turno=t_locked,
            usuario=None,
            nombre_temporal=nom_limpio,
            telefono_temporal=tel_clean,
            tipo_reserva='MANUAL_TEMPORAL',
            es_recurrente=False,
            estado='CONFIRMADA'
        )
        t_locked.cupo_actual = max(0, t_locked.cupo_actual - 1)
        t_locked.save(update_fields=['cupo_actual'])

    try:
        from ..config_loader import obtener_telefonos_alertas_staff
        telefonos_alertas = obtener_telefonos_alertas_staff()
        if telefonos_alertas:
            client = WhatsAppClient()
            msg_duena = (
                f"✦ *Nueva Reserva de Clase de Prueba (Prospecto)* ✦\n\n"
                f"• *Interesada:* {nom_limpio}\n"
                f"• *Teléfono:* +{tel_clean}\n"
                f"• *Clase:* {dia_nom} {fecha_fmt} a las {hora_clean} hs ({turno.clase.nombre}{profe_str})\n"
                f"• *Camilla apartada:* Quedan {t_locked.cupo_actual} libres."
            )
            for tel_staff in telefonos_alertas:
                client.send_text_message(tel_staff, msg_duena)
    except Exception as ex_d:
        logger.warning(f"Error notificando reserva de prueba a Deby: {ex_d}")

    return f"""✦ ¡Bienvenida a Violett Pilates, {nombre_pila}! Ya te apartamos tu camilla de prueba para el *{dia_nom} {fecha_fmt} a las {hora_clean} hs*{profe_str} 🌸.

📍 Te esperamos en *Gral. Guido 1573, Ramos Mejía*.
💡 Te sugerimos venir con ropa cómoda y medias antideslizantes (tenemos vestuario para cambiarte).

¡Cualquier duda avisanos por acá y te ayudamos con mucho gusto! ✨"""


@tool
def anotar_lista_espera_alumna(fecha_o_dia: str, hora_str: str, nombre_o_tel: str = "") -> str:
    """
    Anota a una alumna o interesada en la LISTA DE ESPERA para un turno que ya tiene sus 3 camillas ocupadas (sin cupo).
    Si alguna alumna cancela o se libera una camilla en ese turno, el sistema y la administración podrán contactarla de inmediato.

    Parámetros:
    - fecha_o_dia: 'hoy', 'mañana' o nombre del día/fecha (ej: 'lunes', '24/11', 'viernes').
    - hora_str: Hora de la clase llena (ej: '18:00', '19', '20:00').
    - nombre_o_tel: Nombre o teléfono opcional si no está identificada.
    """
    target_date = resolver_fecha(fecha_o_dia)
    target_time = resolver_hora(hora_str) if hora_str else None

    qs = Turno.objects.filter(fecha=target_date, estado='PROGRAMADO').select_related('clase')
    if target_time:
        qs = qs.filter(hora_inicio__hour=target_time.hour, hora_inicio__minute=target_time.minute)

    turno = qs.first()
    if not turno:
        return f"✦ No encontré una clase programada para el {fecha_o_dia} a las {hora_str} hs."

    from .gestion_tools import get_conversacion_activa, buscar_usuario_por_telefono, get_ultima_alumna_activa
    conv = get_conversacion_activa()
    usuario = None
    if conv and conv.usuario:
        usuario = conv.usuario
    elif conv and conv.telefono:
        usuario = buscar_usuario_por_telefono(conv.telefono)
    if not usuario:
        usuario = get_ultima_alumna_activa()

    tel_alumna = conv.telefono if conv else ""
    nombre_alumna = f"{usuario.nombre} {usuario.apellido}".strip() if usuario else (nombre_o_tel or "Alumna en lista de espera")

    dias_es = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias_es[turno.fecha.weekday()]
    fecha_fmt = turno.fecha.strftime('%d/%m')
    hora_clean = turno.hora_inicio.strftime('%H:%M')

    if conv:
        esperas = conv.metadata.setdefault('lista_espera', [])
        esperas.append({
            'turno_id': str(turno.id),
            'fecha': str(turno.fecha),
            'hora': hora_clean,
            'anotada_en': str(timezone.now())
        })
        conv.save(update_fields=['metadata'])

    try:
        from ..config_loader import obtener_telefonos_alertas_staff
        telefonos_alertas = obtener_telefonos_alertas_staff()
        if telefonos_alertas:
            client = WhatsAppClient()
            msg_duena = (
                f"✦ *Nueva Alumna en Lista de Espera* ✦\n\n"
                f"• *Alumna:* {nombre_alumna} (+{tel_alumna})\n"
                f"• *Clase solicitada:* {dia_nom} {fecha_fmt} a las {hora_clean} hs ({turno.clase.nombre})\n"
                f"• *Estado del turno:* Completo (0 camillas libres).\n"
                f"Si se libera un lugar por cancelación, le avisaremos de inmediato."
            )
            for tel_staff in telefonos_alertas:
                client.send_text_message(tel_staff, msg_duena)
    except Exception as ex_d:
        logger.warning(f"Error notificando lista de espera a Deby: {ex_d}")

    nombre_pila = nombre_alumna.split()[0] if nombre_alumna else ""
    saludo = f"¡Listo {nombre_pila}! ✦ " if nombre_pila else "✦ "

    return f"""{saludo}Te anoté en la *lista de espera* para el *{dia_nom} {fecha_fmt} a las {hora_clean} hs* en {turno.clase.nombre} 🌸.

Si alguna compañera cancela o se libera una camilla en ese bloque, te avisamos de inmediato por acá para que puedas sumarte ✨."""


@tool
def enviar_ubicacion_gps_estudio(telefono_destino: str = "") -> str:
    """
    Envía la ubicación geográfica oficial de Violett Pilates Boutique con pin interactivo de Google Maps directo a WhatsApp.
    Usar cuando una alumna o persona interesada pregunte '¿Dónde quedan?', '¿Cuál es la dirección?', '¿Dónde están ubicados?' o '¿Cómo llego?'.
    """
    from .gestion_tools import get_conversacion_activa
    conv = get_conversacion_activa()
    phone = telefono_destino or (conv.telefono if conv else "")
    if not phone:
        return "📍 Violett Pilates Boutique queda en *Gral. Guido 1573, Ramos Mejía, Provincia de Buenos Aires*."

    try:
        client = WhatsAppClient()
        client.send_location(
            to_number=phone,
            latitude=-34.646875,
            longitude=-58.563722,
            name="Violett Pilates Boutique",
            address="Gral. Guido 1573, Ramos Mejía"
        )
    except Exception as e:
        logger.warning(f"Error enviando ubicación GPS: {e}")

    return "📍 *Violett Pilates Boutique*\n• Dirección: Gral. Guido 1573, Ramos Mejía\n¡Te envié también el pin interactivo en el mapa para que puedas abrirlo directo en Google Maps o Waze! 🌸"


