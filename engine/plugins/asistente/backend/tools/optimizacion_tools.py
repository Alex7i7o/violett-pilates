import datetime
import logging
from django.utils import timezone
from django.db.models import Q
from langchain_core.tools import tool

from core.models import Turno, Reserva, Usuario
from .profesores_tools import resolver_fecha
from ..models import VinculoAlumnos, PreferenciaAlumno, RegistroAccionIA
from ..config_loader import get_asistente_config

logger = logging.getLogger(__name__)

def obtener_pareja_inseparable(usuario: Usuario):
    """
    Retorna el usuario vinculado inseparable si existe y está activo, o None.
    """
    if not usuario:
        return None
    vinculo = VinculoAlumnos.objects.filter(
        Q(alumna_1=usuario) | Q(alumna_2=usuario),
        activo=True,
        tipo='INSEPARABLES'
    ).select_related('alumna_1', 'alumna_2').first()
    
    if not vinculo:
        return None
    return vinculo.alumna_2 if vinculo.alumna_1 == usuario else vinculo.alumna_1


@tool
def analizar_optimizacion_turnos_proximos(fecha_str: str = "mañana") -> str:
    """
    Comando para la dueña del estudio: analiza la ocupación de turnos de una fecha para detectar:
    1. Clases con 1 sola alumna que podrían moverse a una clase adyacente para ahorrar horas de profesora.
    2. Oportunidades de consolidación (varias clases de 2 alumnas que cabrían en menos clases completas de 3).
    3. Respeta estrictamente los vínculos inseparables (ej: madre e hija nunca se separan).
    """
    target_date = resolver_fecha(fecha_str)
    config = get_asistente_config()
    max_cupo = config.get('reglas_operativas', {}).get('max_cupo_por_turno', 3)

    turnos = Turno.objects.filter(
        fecha=target_date,
        estado='PROGRAMADO'
    ).select_related('clase').prefetch_related('reservas__usuario').order_by('hora_inicio')

    if not turnos.exists():
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        dia_nom = dias[target_date.weekday()]
        return f"No hay turnos programados en el sistema para el {dia_nom} {target_date.strftime('%d/%m')}."

    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    dia_nom = dias[target_date.weekday()]

    clases_solitarias = []   # 1 alumna
    clases_parciales = []    # 2 alumnas
    clases_llenas = []       # 3 alumnas
    clases_vacias = []       # 0 alumnas

    info_turnos = []

    for t in turnos:
        reservas_activas = [r for r in t.reservas.all() if r.estado == 'CONFIRMADA']
        cant = len(reservas_activas)
        alumnas_nombres = [r.usuario.nombre or r.usuario.email.split('@')[0] for r in reservas_activas]
        
        info = {
            'turno': t,
            'cant': cant,
            'libres': max_cupo - cant,
            'reservas': reservas_activas,
            'alumnas': alumnas_nombres
        }
        info_turnos.append(info)

        if cant == 0:
            clases_vacias.append(info)
        elif cant == 1:
            clases_solitarias.append(info)
        elif cant == 2:
            clases_parciales.append(info)
        elif cant >= max_cupo:
            clases_llenas.append(info)

    lineas_resumen = [
        f"✦ *Análisis de Ocupación para el {dia_nom} {target_date.strftime('%d/%m')}:*",
        f"• Total clases programadas: {len(turnos)}",
        f"• Clases 100% llenas ({max_cupo}/{max_cupo}): {len(clases_llenas)}",
        f"• Clases con {max_cupo - 1} alumnas (1 libre): {len(clases_parciales)}",
        f"• Clases con 1 sola alumna: {len(clases_solitarias)}",
        f"• Clases sin reservas: {len(clases_vacias)}",
        ""
    ]

    sugerencias = []

    # 1. Analizar clases con 1 sola alumna
    for sol in clases_solitarias:
        reserva = sol['reservas'][0]
        alumna = reserva.usuario
        pareja = obtener_pareja_inseparable(alumna)
        hora_sol = sol['turno'].hora_inicio.strftime('%H:%M')

        # Buscar turno adyacente o cercano con lugar
        candidatos_reubicacion = []
        for other in info_turnos:
            if other['turno'].id == sol['turno'].id:
                continue
            if other['libres'] >= (2 if pareja else 1):
                candidatos_reubicacion.append(other)

        if candidatos_reubicacion:
            mejor = candidatos_reubicacion[0]
            hora_dest = mejor['turno'].hora_inicio.strftime('%H:%M')
            pareja_txt = f" y su vínculo ({pareja.nombre})" if pareja else ""
            sugerencias.append(
                f"👉 *Mover clase solitaria de las {hora_sol} hs:*\n"
                f"   *{alumna.nombre}*{pareja_txt} está sola a las {hora_sol} hs.\n"
                f"   Podés sumarla a las *{hora_dest} hs* (hay {mejor['libres']} camilla/s libre/s con {', '.join(mejor['alumnas'])}). "
                f"Así se libera 1 hora de profesora."
            )
        else:
            sugerencias.append(
                f"👉 *Clase solitaria {hora_sol} hs:*\n"
                f"   *{alumna.nombre}* está sola. No hay otros turnos con cupo libre en ese día, sugerido mantener o consultar disponibilidad otro día."
            )

    # 2. Analizar múltiples clases con 2 alumnas
    if len(clases_parciales) >= 2:
        horas_parciales = [c['turno'].hora_inicio.strftime('%H:%M') for c in clases_parciales]
        total_alumnas_parciales = len(clases_parciales) * 2
        clases_necesarias = (total_alumnas_parciales + max_cupo - 1) // max_cupo
        ahorro_horas = len(clases_parciales) - clases_necesarias

        if ahorro_horas > 0:
            sugerencias.append(
                f"💡 *Oportunidad de consolidación de horarios:*\n"
                f"   Hay {len(clases_parciales)} clases con 2 alumnas ({', '.join(horas_parciales)} hs). "
                f"En total son {total_alumnas_parciales} alumnas que caben en solo {clases_necesarias} clases de {max_cupo} camillas. "
                f"Si agrupás los horarios, ¡ahorrás {ahorro_horas} hora/s de pago a profesoras!"
            )

    if sugerencias:
        lineas_resumen.append("⚡ *RECOMENDACIONES DE OPTIMIZACIÓN:*")
        lineas_resumen.extend(sugerencias)
    else:
        lineas_resumen.append("✅ La distribución de alumnas está óptima. No se requieren cambios para este día.")

    # Registrar en acciones de IA
    RegistroAccionIA.objects.create(
        tipo_accion='PROPUESTA_CONSOLIDACION',
        descripcion=f"Análisis de ocupación y sugerencias de consolidación generado para {target_date}.",
        payload={
            'fecha': str(target_date),
            'clases_solitarias': len(clases_solitarias),
            'clases_parciales': len(clases_parciales),
            'sugerencias_count': len(sugerencias)
        }
    )

    return "\n".join(lineas_resumen)


@tool
def vincular_alumnas_inseparables(alumna1_nombre_o_tel: str, alumna2_nombre_o_tel: str, observaciones: str = "Vienen juntas siempre (Madre e hija / Amigas)") -> str:
    """
    Comando administrativo para la dueña: vincula a dos alumnas como pareja inseparable (ej: madre e hija, amigas íntimas).
    El sistema garantiza que el optimizador de turnos nunca las separe en horarios distintos ni mueva a una sin la otra.
    """
    clean_1 = alumna1_nombre_o_tel.strip().lower()
    clean_2 = alumna2_nombre_o_tel.strip().lower()

    u1 = Usuario.objects.filter(Q(nombre__icontains=clean_1) | Q(telefono__icontains=clean_1)).first()
    u2 = Usuario.objects.filter(Q(nombre__icontains=clean_2) | Q(telefono__icontains=clean_2)).first()

    if not u1:
        return f"No encontré a la alumna '{alumna1_nombre_o_tel}' en el sistema."
    if not u2:
        return f"No encontré a la alumna '{alumna2_nombre_o_tel}' en el sistema."

    if u1.id == u2.id:
        return "No podés vincular a una alumna consigo misma."

    vinculo, created = VinculoAlumnos.objects.update_or_create(
        alumna_1=u1,
        alumna_2=u2,
        defaults={
            'tipo': 'INSEPARABLES',
            'observaciones': observaciones,
            'activo': True
        }
    )

    accion = "creado" if created else "actualizado"
    return (
        f"✦ Vínculo inseparable {accion} con éxito:\n"
        f"• Alumnas: *{u1.nombre} {u1.apellido}* + *{u2.nombre} {u2.apellido}*\n"
        f"• Regla: *Inseparables* ({observaciones})\n"
        f"El optimizador y el recepcionista IA respetarán que asistan siempre juntas y nunca las separarán en horarios distintos."
    )


@tool
def guardar_preferencia_alumna(nombre_o_tel: str, franja: str = "INDIFERENTE", notas: str = "") -> str:
    """
    Registra o actualiza las preferencias personales de una alumna (franja horaria: 'MANANA', 'TARDE', 'NOCHE' o 'INDIFERENTE', notas de patologías, lesiones o preferencias).
    """
    clean = nombre_o_tel.strip().lower()
    u = Usuario.objects.filter(Q(nombre__icontains=clean) | Q(telefono__icontains=clean)).first()
    if not u:
        return f"No encontré a la alumna '{nombre_o_tel}' en el sistema."

    franja_normalizada = franja.upper().strip()
    if franja_normalizada not in ['MANANA', 'TARDE', 'NOCHE', 'INDIFERENTE']:
        if 'mañan' in clean or 'manan' in clean:
            franja_normalizada = 'MANANA'
        elif 'tard' in clean:
            franja_normalizada = 'TARDE'
        elif 'noch' in clean:
            franja_normalizada = 'NOCHE'
        else:
            franja_normalizada = 'INDIFERENTE'

    pref, _ = PreferenciaAlumno.objects.update_or_create(
        usuario=u,
        defaults={
            'franja_preferida': franja_normalizada,
            'notas_asistente': notas
        }
    )

    return f"✦ Preferencias guardadas para *{u.nombre}*:\n• Franja horaria: {pref.get_franja_preferida_display()}\n• Notas: {notas or 'Sin notas adicionales'}."


@tool
def consultar_preferencias_o_vinculos(nombre_o_tel: str) -> str:
    """
    Consulta las preferencias horarias y vínculos de una alumna en el sistema.
    """
    clean = nombre_o_tel.strip().lower()
    u = Usuario.objects.filter(Q(nombre__icontains=clean) | Q(telefono__icontains=clean)).first()
    if not u:
        return f"No encontré a la alumna '{nombre_o_tel}'."

    pareja = obtener_pareja_inseparable(u)
    vinculo_txt = f"Inseparable de *{pareja.nombre} {pareja.apellido}* (deben asistir juntas)." if pareja else "Sin vínculos inseparables registrados."

    pref = getattr(u, 'preferencias_ia', None)
    franja_txt = pref.get_franja_preferida_display() if pref else "Sin franja especificada (Flexible)"
    notas_txt = pref.notas_asistente if pref and pref.notas_asistente else "Ninguna"

    return (
        f"✦ Perfil de Preferencias de *{u.nombre} {u.apellido}*:\n"
        f"• Vínculo inseparable: {vinculo_txt}\n"
        f"• Franja preferida: {franja_txt}\n"
        f"• Notas de atención: {notas_txt}"
    )
