import { api } from './api';

export interface Profesor {
    id: string;
    nombre: string;
    apellido: string;
    telefono: string;
    email: string;
    especialidad: string;
    color_identificador: string;
    is_active: boolean;
}

export interface ReservaAdmin {
    id: string;
    alumno_id: string;
    alumno_nombre: string;
    alumno_apellido: string;
    estado: string;
    es_recurrente: boolean;
}

export interface TurnoAdmin {
    id: string;
    fecha: string;
    hora_inicio: string;
    hora_fin: string;
    cupo_actual: number;
    estado: string;
    clase: string;
    clase_nombre: string;
    profesor?: Profesor;
    profesor_id?: string;
    reservas_list: ReservaAdmin[];
}

export interface PlanActivo {
    id: string;
    nombre: string;
    clases_restantes: number;
    fecha_vencimiento: string;
}

export interface UsuarioAdmin {
    id: string;
    nombre: string;
    apellido: string;
    email: string;
    telefono: string;
    contacto_emergencia: string;
    notas_medicas: string;
    is_active: boolean;
    plan_activo: PlanActivo | null;
}

// APIs
export const getAdminProfesores = () => api.get<Profesor[]>('/admin/profesores/');
export const createAdminProfesor = (data: any) => api.post('/admin/profesores/', data);
export const updateAdminProfesor = (id: string, data: any) => api.patch(`/admin/profesores/${id}/`, data);
export const deleteAdminProfesor = (id: string) => api.delete(`/admin/profesores/${id}/`);

export const getAdminAgenda = (fecha: string) => api.get<TurnoAdmin[]>(`/admin/agenda/?fecha=${fecha}`);
export const createAdminTurno = (data: any) => api.post('/admin/turnos/', data);
export const deleteAdminTurno = (id: string) => api.delete(`/admin/turnos/${id}/`);

export const updateAsistencia = (id: string, estado: 'TOMADA' | 'AUSENTE') => api.patch(`/admin/reservas/${id}/asistencia/`, { estado });

export const getAdminAlumnos = (search: string = '') => api.get<UsuarioAdmin[]>(`/admin/alumnos/?q=${search}`);
export const createAdminAlumno = (data: any) => api.post('/admin/alumnos/', data);
export const getAdminAlumnoDetalle = (id: string) => api.get<UsuarioAdmin>(`/admin/alumnos/${id}/`);
export const asignarPlanAlumno = (id: string, plan_id: string) => api.post(`/admin/alumnos/${id}/asignar-plan/`, { plan_id });
