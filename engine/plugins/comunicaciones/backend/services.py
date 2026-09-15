def notificar_cancelacion_clase(usuario, turno):
    print(f"[MAIL A {usuario.email}] LAMENTAMOS INFORMARLE QUE LA CLASE DE {turno.clase.nombre} DEL {turno.fecha.strftime('%d/%m')} A LAS {turno.hora_inicio.strftime('%H:%M')} FUE CANCELADA POR NO ALCANZAR EL CUPO MINIMO.")

def notificar_recordatorio_asistencia(usuario, turno):
    print(f"[MAIL A {usuario.email}] RECORDATORIO: SU CLASE DE {turno.clase.nombre} ES MAÑANA A LAS {turno.hora_inicio.strftime('%H:%M')}. LO ESPERAMOS.")

def notificar_alerta_cupo(usuarios, turno):
    emails = [u.email for u in usuarios]
    print(f"[MAIL A {', '.join(emails)}] URGENTE: LA CLASE DE {turno.clase.nombre} MAÑANA A LAS {turno.hora_inicio.strftime('%H:%M')} ESTA A PUNTO DE CANCELARSE POR FALTA DE ALUMNOS! INSCRIBETE AHORA Y SALVA LA CLASE.")
