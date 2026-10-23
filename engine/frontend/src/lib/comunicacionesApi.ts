import { api } from './api';

export interface ConversacionCRM {
  id: string;
  telefono: string;
  usuario_id: string | null;
  nombre: string;
  rol_detectado: 'ALUMNA' | 'PROFESOR' | 'DUENA' | 'PROSPECTO';
  estado: 'ACTIVO' | 'ESPERANDO_HUMANO' | 'CERRADO';
  ultimo_mensaje: string;
  ultimo_mensaje_at: string;
  total_mensajes: number;
}

export interface MensajeCRM {
  id: string;
  direccion: 'ENTRANTE' | 'SALIENTE';
  agente_responsable: string;
  texto: string;
  tools_ejecutadas: string[];
  created_at: string;
}

export interface EmailLog {
  id: string;
  destinatario: string;
  asunto: string;
  template_name: string;
  estado: 'ENVIADO' | 'FALLIDO';
  error_mensaje: string;
  cuerpo_texto: string;
  cuerpo_html?: string;
  created_at: string;
}

export const getConversaciones = (q: string = '', rol: string = '') =>
  api.get<ConversacionCRM[]>('/admin/asistente/conversaciones/', {
    params: { q: q || undefined, rol: rol || undefined }
  });

export const getMensajes = (conversacionId: string) =>
  api.get<MensajeCRM[]>(`/admin/asistente/conversaciones/${conversacionId}/mensajes/`);

export const togglePausaIA = (conversacionId: string) =>
  api.post<{ detail: string; estado: 'ACTIVO' | 'ESPERANDO_HUMANO' }>(
    `/admin/asistente/conversaciones/${conversacionId}/pausar/`
  );

export const enviarMensajeManual = (conversacionId: string, texto: string) =>
  api.post<MensajeCRM>(`/admin/asistente/conversaciones/${conversacionId}/enviar/`, { texto });

export const getEmailLogs = (q: string = '', estado: string = '') =>
  api.get<EmailLog[]>('/admin/comunicaciones/emails/', {
    params: { q: q || undefined, estado: estado || undefined }
  });

export const getEmailLogDetail = (id: string) =>
  api.get<EmailLog>(`/admin/comunicaciones/emails/${id}/`);
