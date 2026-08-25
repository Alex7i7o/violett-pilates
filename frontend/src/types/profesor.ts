export interface ClaseProfesor {
  id: string;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  clase_nombre: string;
  estado?: string;
}

export interface PlantillaProfesor {
  id: string;
  dia_semana: number;
  hora_inicio: string;
  hora_fin: string;
  clase_nombre: string;
}

export interface ProfesorDashboardData {
  mis_plantillas: PlantillaProfesor[];
  horas_mes: number;
  turnos_mes_historial: ClaseProfesor[];
  turnos_hoy: ClaseProfesor[];
  turnos_semana: ClaseProfesor[];
  turnos_libres: ClaseProfesor[];
  plantillas_libres: PlantillaProfesor[];
}
