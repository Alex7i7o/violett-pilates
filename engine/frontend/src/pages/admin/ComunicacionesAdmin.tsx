import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { 
  getConversaciones, 
  getMensajes, 
  togglePausaIA, 
  enviarMensajeManual, 
  getEmailLogs, 
  getEmailLogDetail,
  getErroresIA,
  toggleResolverErrorIA,
  resolverTodosErroresIA
} from '../../lib/comunicacionesApi';
import type { ConversacionCRM, MensajeCRM, EmailLog, RegistroErrorIAItem } from '../../lib/comunicacionesApi';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Modal } from '../../components/ui/Modal';
import { 
  ArrowLeft,
  MessageSquare, 
  Mail, 
  Search, 
  Send, 
  Bot, 
  User, 
  PauseCircle, 
  PlayCircle, 
  RefreshCw, 
  CheckCircle2, 
  CheckCircle,
  AlertCircle, 
  AlertTriangle,
  Terminal,
  ShieldCheck,
  ChevronDown,
  ChevronUp, 
  Clock, 
  Eye, 
  Sparkles,
  Phone,
  Copy,
  Download
} from 'lucide-react';

export function ComunicacionesAdmin() {
  const [activeTab, setActiveTab] = useState<'whatsapp' | 'emails' | 'errores'>('whatsapp');

  // ==========================================
  // ESTADOS WHATSAPP CRM
  // ==========================================
  const [conversaciones, setConversaciones] = useState<ConversacionCRM[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<string | null>(null);
  const [mobileView, setMobileView] = useState<'list' | 'chat'>('list');
  const [mensajes, setMensajes] = useState<MensajeCRM[]>([]);
  const [loadingConv, setLoadingConv] = useState(true);
  const [loadingMsgs, setLoadingMsgs] = useState(false);
  const [searchConv, setSearchConv] = useState('');
  const [rolFilter, setRolFilter] = useState('');
  const [nuevoMensajeTexto, setNuevoMensajeTexto] = useState('');
  const [isSendingMsg, setIsSendingMsg] = useState(false);
  const [isTogglingPausa, setIsTogglingPausa] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const isUserNearBottomRef = useRef<boolean>(true);
  const shouldForceScrollRef = useRef<boolean>(false);
  const prevConvIdRef = useRef<string | null>(null);
  const [showScrollBottomBtn, setShowScrollBottomBtn] = useState(false);

  // ==========================================
  // ESTADOS HISTORIAL DE EMAILS
  // ==========================================
  const [emailLogs, setEmailLogs] = useState<EmailLog[]>([]);
  const [loadingEmails, setLoadingEmails] = useState(false);
  const [searchEmail, setSearchEmail] = useState('');
  const [estadoEmailFilter, setEstadoEmailFilter] = useState('');
  const [selectedEmailDetail, setSelectedEmailDetail] = useState<EmailLog | null>(null);
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);
  const [loadingEmailDetail, setLoadingEmailDetail] = useState(false);

  // ==========================================
  // ESTADOS DIAGNÓSTICO Y ERRORES IA (CENTINELA)
  // ==========================================
  const [erroresIA, setErroresIA] = useState<RegistroErrorIAItem[]>([]);
  const [loadingErrores, setLoadingErrores] = useState(false);
  const [searchError, setSearchError] = useState('');
  const [verResueltos, setVerResueltos] = useState(false);
  const [expandedErrorId, setExpandedErrorId] = useState<string | null>(null);

  // ==========================================
  // EFECTOS Y CARGA DE DATOS
  // ==========================================
  const fetchConversacionesData = async (silent = false) => {
    if (!silent) setLoadingConv(true);
    try {
      const res = await getConversaciones(searchConv, rolFilter);
      setConversaciones(res.data);
      if (!selectedConvId && res.data.length > 0) {
        setSelectedConvId(res.data[0].id);
      }
    } catch (e) {
      console.error(e);
      if (!silent) toast.error('Error al cargar conversaciones de WhatsApp');
    } finally {
      if (!silent) setLoadingConv(false);
    }
  };

  const fetchMensajesData = async (convId: string, silent = false) => {
    if (!silent) setLoadingMsgs(true);
    try {
      const res = await getMensajes(convId);
      setMensajes(prev => {
        // En polling silencioso, si los mensajes no cambiaron, preservar la referencia para no alterar el scroll del usuario
        if (silent && prev.length === res.data.length && prev.length > 0) {
          const lastPrev = prev[prev.length - 1];
          const lastNew = res.data[res.data.length - 1];
          if (lastPrev.id === lastNew.id && lastPrev.texto === lastNew.texto) {
            return prev;
          }
        }
        return res.data;
      });
    } catch (e) {
      console.error(e);
      if (!silent) toast.error('Error al cargar mensajes');
    } finally {
      if (!silent) setLoadingMsgs(false);
    }
  };

  const fetchEmailLogsData = async () => {
    setLoadingEmails(true);
    try {
      const res = await getEmailLogs(searchEmail, estadoEmailFilter);
      setEmailLogs(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Error al cargar historial de correos');
    } finally {
      setLoadingEmails(false);
    }
  };

  const fetchErroresData = async () => {
    setLoadingErrores(true);
    try {
      const res = await getErroresIA(verResueltos, searchError);
      setErroresIA(res.data);
    } catch (e) {
      console.error(e);
      toast.error('Error al cargar la bitácora de errores');
    } finally {
      setLoadingErrores(false);
    }
  };

  const handleToggleResolver = async (errorId: string) => {
    try {
      const res = await toggleResolverErrorIA(errorId);
      toast.success(res.data.detail);
      setErroresIA(prev => {
        if (!verResueltos && res.data.resuelto) {
          return prev.filter(item => item.id !== errorId);
        }
        return prev.map(item => item.id === errorId ? { ...item, resuelto: res.data.resuelto } : item);
      });
    } catch (e) {
      toast.error('Error al actualizar estado del ticket');
    }
  };

  const handleResolverTodos = async () => {
    try {
      const res = await resolverTodosErroresIA();
      toast.success(res.data.detail);
      if (!verResueltos) {
        setErroresIA([]);
      } else {
        setErroresIA(prev => prev.map(item => ({ ...item, resuelto: true })));
      }
    } catch (e) {
      toast.error('Error al resolver todos los tickets');
    }
  };

  const handleExportarErrores = () => {
    if (erroresIA.length === 0) {
      toast.info('No hay errores para exportar.');
      return;
    }

    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const lineas = [
      '=======================================================',
      'BITÁCORA CENTINELA - REPORTE DE ERRORES Y DIAGNÓSTICO IA',
      `Fecha de exportación: ${new Date().toLocaleString()}`,
      `Total de tickets exportados: ${erroresIA.length}`,
      '=======================================================\n'
    ];

    erroresIA.forEach((item, idx) => {
      lineas.push('-------------------------------------------------------');
      lineas.push(`[${idx + 1}] TICKET: ${item.ticket} | ESTADO: ${item.resuelto ? 'RESUELTO' : 'ACTIVO'}`);
      lineas.push(`Fecha: ${item.created_at}`);
      lineas.push(`Rol: ${item.rol_usuario} ${item.telefono ? `(${item.telefono})` : ''}`);
      lineas.push(`Agente responsable: ${item.agente_responsable}`);
      lineas.push(`Tipo de fallo: ${item.tipo_error}`);
      if (item.mensaje_usuario) {
        lineas.push(`Mensaje de la usuaria: "${item.mensaje_usuario}"`);
      }
      lineas.push(`Diagnóstico Centinela: ${item.diagnostico_ia || 'N/A'}`);
      lineas.push(`Error técnico: ${item.detalle_error}`);
      if (item.traceback_completo) {
        lineas.push(`\nTraceback completo:\n${item.traceback_completo}`);
      }
      lineas.push('\n');
    });

    const textoFinal = lineas.join('\n');

    // 1. Descargar archivo .txt
    const blob = new Blob([textoFinal], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `bitacora_errores_ia_${timestamp}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    // 2. Copiar al portapapeles para pasar rápido por chat
    if (navigator.clipboard) {
      navigator.clipboard.writeText(textoFinal).then(() => {
        toast.success('¡Reporte descargado y copiado al portapapeles!');
      }).catch(() => {
        toast.success('¡Archivo de errores descargado!');
      });
    } else {
      toast.success('¡Archivo de errores descargado!');
    }
  };

  // Carga inicial y filtros de WhatsApp
  useEffect(() => {
    if (activeTab === 'whatsapp') {
      fetchConversacionesData();
    } else if (activeTab === 'emails') {
      fetchEmailLogsData();
    } else if (activeTab === 'errores') {
      fetchErroresData();
    }
  }, [activeTab, rolFilter, verResueltos]);

  // Carga de mensajes al seleccionar conversación
  useEffect(() => {
    if (selectedConvId) {
      fetchMensajesData(selectedConvId);
    }
  }, [selectedConvId]);

  // Polling suave de WhatsApp cada 7 segundos sólo si la pestaña del navegador está activa
  useEffect(() => {
    if (activeTab !== 'whatsapp') return;

    const interval = setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchConversacionesData(true);
        if (selectedConvId) {
          fetchMensajesData(selectedConvId, true);
        }
      }
    }, 7000);

    return () => clearInterval(interval);
  }, [activeTab, selectedConvId]);

  // Control inteligente de scroll en el chat
  const handleChatScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    // Si la distancia al fondo es menor a 120px, el usuario está al final
    const isNearBottom = scrollHeight - scrollTop - clientHeight < 120;
    isUserNearBottomRef.current = isNearBottom;
    setShowScrollBottomBtn(!isNearBottom);
  };

  const scrollToBottom = (smooth = true) => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
      });
      isUserNearBottomRef.current = true;
      setShowScrollBottomBtn(false);
    }
  };

  // Auto-scroll que respeta la lectura del usuario (NUNCA lo devuelve abajo si scrolleó para leer)
  useEffect(() => {
    const isDifferentConv = prevConvIdRef.current !== selectedConvId;
    prevConvIdRef.current = selectedConvId;

    if (isDifferentConv) {
      // Cambio de conversación: scrollear al final inmediatamente
      setTimeout(() => scrollToBottom(false), 50);
      isUserNearBottomRef.current = true;
      setShowScrollBottomBtn(false);
      return;
    }

    // Misma conversación: SOLO scrollear abajo si el usuario ya estaba abajo o forzó un envío
    if (shouldForceScrollRef.current || isUserNearBottomRef.current) {
      scrollToBottom(true);
      shouldForceScrollRef.current = false;
    }
  }, [mensajes, selectedConvId]);

  // Handler para buscar conversaciones con enter o botón
  const handleSearchConvSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchConversacionesData();
  };

  // Handler para buscar emails
  const handleSearchEmailSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchEmailLogsData();
  };

  // Handler para pausar / reactivar bot
  const handleTogglePausa = async () => {
    if (!selectedConvId) return;
    try {
      setIsTogglingPausa(true);
      const res = await togglePausaIA(selectedConvId);
      setConversaciones(prev => prev.map(c => c.id === selectedConvId ? { ...c, estado: res.data.estado } : c));
      toast.success(res.data.estado === 'ESPERANDO_HUMANO' ? 'IA Pausada para este contacto' : 'IA Reanudada exitosamente');
    } catch (e) {
      toast.error('Error al cambiar estado de la IA');
    } finally {
      setIsTogglingPausa(false);
    }
  };

  // Handler para exportar o copiar el chat de la conversación activa
  const handleCopiarChat = () => {
    if (!selectedConv || mensajes.length === 0) {
      toast.error('No hay mensajes en esta conversación para copiar.');
      return;
    }

    const header = [
      `==================================================`,
      `CONVERSACIÓN WHATSAPP - VIOLETT PILATES`,
      `Contacto: ${selectedConv.nombre} (${selectedConv.telefono})`,
      `Rol: ${selectedConv.rol_detectado} | Estado: ${selectedConv.estado === 'ESPERANDO_HUMANO' ? 'Atención Humana' : 'IA Activa'}`,
      `Total Mensajes: ${mensajes.length}`,
      `Exportado el: ${new Date().toLocaleString('es-AR')}`,
      `==================================================\n`
    ].join('\n');

    const lines = mensajes.map((m) => {
      const remitente = m.direccion === 'ENTRANTE' 
        ? `[${selectedConv.nombre || 'Clienta'}]` 
        : m.agente_responsable === 'humano_admin' 
        ? `[Administración (Manual)]` 
        : `[IA (${m.agente_responsable || 'asistente'})]`;
      const tools = m.tools_ejecutadas && m.tools_ejecutadas.length > 0 
        ? ` (Tools: ${m.tools_ejecutadas.join(', ')})` 
        : '';
      return `${m.created_at} ${remitente}${tools}:\n${m.texto}\n`;
    });

    const fullTranscript = `${header}\n${lines.join('\n')}`;

    navigator.clipboard.writeText(fullTranscript).then(() => {
      toast.success('¡Conversación copiada al portapapeles! 📋 Pegala directamente acá en el chat.');
    }).catch(() => {
      toast.error('No se pudo copiar automáticamente.');
    });
  };

  const handleDescargarChat = () => {
    if (!selectedConv || mensajes.length === 0) {
      toast.error('No hay mensajes para descargar.');
      return;
    }

    const header = [
      `==================================================`,
      `CONVERSACIÓN WHATSAPP - VIOLETT PILATES`,
      `Contacto: ${selectedConv.nombre} (${selectedConv.telefono})`,
      `Rol: ${selectedConv.rol_detectado} | Estado: ${selectedConv.estado === 'ESPERANDO_HUMANO' ? 'Atención Humana' : 'IA Activa'}`,
      `Total Mensajes: ${mensajes.length}`,
      `Exportado el: ${new Date().toLocaleString('es-AR')}`,
      `==================================================\n`
    ].join('\n');

    const lines = mensajes.map((m) => {
      const remitente = m.direccion === 'ENTRANTE' 
        ? `[${selectedConv.nombre || 'Clienta'}]` 
        : m.agente_responsable === 'humano_admin' 
        ? `[Administración (Manual)]` 
        : `[IA (${m.agente_responsable || 'asistente'})]`;
      const tools = m.tools_ejecutadas && m.tools_ejecutadas.length > 0 
        ? ` (Tools: ${m.tools_ejecutadas.join(', ')})` 
        : '';
      return `${m.created_at} ${remitente}${tools}:\n${m.texto}\n`;
    });

    const fullTranscript = `${header}\n${lines.join('\n')}`;
    const cleanPhone = selectedConv.telefono.replace(/[^0-9]/g, '');
    const dateStr = new Date().toISOString().slice(0, 10);
    const fileName = `chat_${selectedConv.nombre.replace(/\s+/g, '_')}_${cleanPhone}_${dateStr}.txt`;

    const blob = new Blob([fullTranscript], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    toast.success(`Chat descargado como ${fileName} 📥`);
  };

  // Handler para enviar mensaje manual por WhatsApp
  const handleEnviarMensaje = async (e: React.FormEvent) => {
    shouldForceScrollRef.current = true;
    e.preventDefault();
    if (!selectedConvId || !nuevoMensajeTexto.trim()) return;

    const texto = nuevoMensajeTexto.trim();
    setNuevoMensajeTexto('');
    try {
      setIsSendingMsg(true);
      const res = await enviarMensajeManual(selectedConvId, texto);
      setMensajes(prev => [...prev, res.data]);
      toast.success('Mensaje enviado por WhatsApp');
      fetchConversacionesData(true);
    } catch (e: any) {
      console.error(e);
      toast.error(e.response?.data?.detail || 'Error al enviar mensaje por WhatsApp');
    } finally {
      setIsSendingMsg(false);
    }
  };

  // Handler para ver detalle del email
  const handleVerEmail = async (emailId: string) => {
    setIsEmailModalOpen(true);
    setLoadingEmailDetail(true);
    try {
      const res = await getEmailLogDetail(emailId);
      setSelectedEmailDetail(res.data);
    } catch (e) {
      toast.error('Error al cargar contenido del correo');
      setIsEmailModalOpen(false);
    } finally {
      setLoadingEmailDetail(false);
    }
  };

  const selectedConv = conversaciones.find(c => c.id === selectedConvId);

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
      {/* Encabezado */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold text-primary-main flex items-center gap-2">
            <span>Comunicaciones</span>
          </h1>
          <p className="text-xs text-muted mt-0.5">
            Supervisión en tiempo real de WhatsApp con IA y auditoría de correos electrónicos.
          </p>
        </div>

        {/* Selector de Pestañas */}
        <div className="flex bg-slate-100 p-1 rounded-2xl border border-slate-200 w-full sm:w-auto">
          <button
            onClick={() => setActiveTab('whatsapp')}
            className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-3 sm:px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'whatsapp'
                ? 'bg-primary-main text-white shadow-sm'
                : 'text-slate-600 hover:text-primary-main hover:bg-white/50'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            <span>WhatsApp en Vivo</span>
          </button>
          <button
            onClick={() => setActiveTab('emails')}
            className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-3 sm:px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'emails'
                ? 'bg-primary-main text-white shadow-sm'
                : 'text-slate-600 hover:text-primary-main hover:bg-white/50'
            }`}
          >
            <Mail className="w-4 h-4" />
            <span>Historial de Emails</span>
          </button>
          <button
            onClick={() => setActiveTab('errores')}
            className={`flex-1 sm:flex-initial flex items-center justify-center gap-2 px-3 sm:px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'errores'
                ? 'bg-slate-900 text-white shadow-sm'
                : 'text-slate-600 hover:text-rose-700 hover:bg-white/50'
            }`}
          >
            <AlertTriangle className={`w-4 h-4 ${activeTab === 'errores' ? 'text-amber-400' : 'text-amber-500'}`} />
            <span>Diagnóstico y Errores IA</span>
            {erroresIA.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-rose-600 text-white font-extrabold">
                {erroresIA.length}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* ======================================================== */}
      {/* PESTAÑA 1: WHATSAPP CRM (ESTILO WHATSAPP WEB)            */}
      {/* ======================================================== */}
      {activeTab === 'whatsapp' && (
        <Card className="border-primary-light/50 overflow-hidden shadow-sm">
          <CardContent className="p-0">
            <div className="flex flex-col md:flex-row h-[calc(100dvh-175px)] md:h-[calc(100vh-210px)] min-h-[460px] md:min-h-[580px] bg-slate-50">
              
              {/* COLUMNA IZQUIERDA: LISTA DE CHATS */}
              <div className={`w-full md:w-80 lg:w-96 border-r border-slate-200 flex flex-col bg-white shrink-0 ${
                mobileView === 'chat' ? 'hidden md:flex' : 'flex'
              }`}>
                
                {/* Buscador y Filtros */}
                <div className="p-3 border-b border-slate-100 space-y-2 bg-slate-50/70">
                  <form onSubmit={handleSearchConvSubmit} className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted" />
                    <input
                      type="text"
                      placeholder="Buscar chat o teléfono..."
                      value={searchConv}
                      onChange={(e) => setSearchConv(e.target.value)}
                      className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-primary-main bg-white"
                    />
                  </form>

                  {/* Pills de Rol */}
                  <div className="flex items-center gap-1 overflow-x-auto pb-1 text-[11px] hide-scrollbar">
                    {['', 'ALUMNA', 'PROSPECTO', 'PROFESOR', 'DUENA'].map((r) => {
                      const label = r === '' ? 'Todos' : r === 'ALUMNA' ? 'Alumnas' : r === 'PROSPECTO' ? 'Prospectos' : r === 'PROFESOR' ? 'Profes' : 'Dueña';
                      const isSelected = rolFilter === r;
                      return (
                        <button
                          key={r}
                          onClick={() => setRolFilter(r)}
                          className={`px-2.5 py-1 rounded-lg font-semibold whitespace-nowrap transition-colors ${
                            isSelected
                              ? 'bg-primary-main text-white'
                              : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-100'
                          }`}
                        >
                          {label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Lista de Conversaciones */}
                <div className="flex-1 overflow-y-auto divide-y divide-slate-100 custom-scrollbar">
                  {loadingConv ? (
                    <div className="p-6 text-center text-xs text-muted">
                      <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-primary-main" />
                      Cargando conversaciones...
                    </div>
                  ) : conversaciones.length === 0 ? (
                    <div className="p-6 text-center text-xs text-muted">
                      No se encontraron conversaciones.
                    </div>
                  ) : (
                    conversaciones.map((conv) => {
                      const isSelected = selectedConvId === conv.id;
                      const isPausado = conv.estado === 'ESPERANDO_HUMANO';

                      return (
                        <button
                          key={conv.id}
                          onClick={() => {
                            setSelectedConvId(conv.id);
                            setMobileView('chat');
                          }}
                          className={`w-full text-left p-3.5 transition-all flex items-start gap-3 hover:bg-slate-50/80 ${
                            isSelected ? 'bg-primary-light/35 border-l-4 border-primary-main shadow-2xs' : ''
                          }`}
                        >
                          {/* Avatar */}
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shrink-0 shadow-2xs ${
                            isPausado ? 'bg-amber-100 text-amber-800' : 'bg-primary-light text-primary-main'
                          }`}>
                            {conv.nombre.charAt(0).toUpperCase() || '✦'}
                          </div>

                          {/* Info */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-1 mb-1">
                              <h4 className="text-xs font-bold text-foreground truncate">{conv.nombre}</h4>
                              <span className="text-[10px] text-muted shrink-0 font-medium">{conv.ultimo_mensaje_at}</span>
                            </div>

                            <p className="text-xs text-muted truncate leading-relaxed">{conv.ultimo_mensaje || 'Sin mensajes aún'}</p>

                            <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                              {/* Rol Badge */}
                              <span className="text-[9px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                                {conv.rol_detectado}
                              </span>

                              {/* Estado Badge */}
                              {isPausado ? (
                                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 flex items-center gap-0.5">
                                  <User className="w-2.5 h-2.5" /> Humano
                                </span>
                              ) : (
                                <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-0.5">
                                  <Sparkles className="w-2.5 h-2.5" /> IA Activa
                                </span>
                              )}
                            </div>
                          </div>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>

              {/* COLUMNA DERECHA: VENTANA DE CHAT */}
              <div className={`flex-1 flex flex-col bg-slate-100/60 h-full min-w-0 ${
                mobileView === 'list' ? 'hidden md:flex' : 'flex'
              }`}>
                {selectedConv ? (
                  <>
                    {/* Header del Chat */}
                    <div className="p-3 sm:p-3.5 bg-white border-b border-slate-200 flex items-center justify-between gap-2 sm:gap-3 shadow-2xs">
                      <div className="flex items-center gap-2 sm:gap-3 min-w-0">
                        <button
                          type="button"
                          onClick={() => setMobileView('list')}
                          className="md:hidden p-2 -ml-1 text-slate-600 hover:text-foreground hover:bg-slate-100 rounded-xl transition-colors shrink-0"
                          aria-label="Volver a lista de chats"
                        >
                          <ArrowLeft className="w-5 h-5" />
                        </button>
                        <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-primary-light text-primary-main flex items-center justify-center font-bold text-sm shrink-0">
                          {selectedConv.nombre.charAt(0).toUpperCase() || '✦'}
                        </div>
                        <div className="min-w-0">
                          <h3 className="font-bold text-xs sm:text-sm text-foreground truncate flex items-center gap-1.5 sm:gap-2">
                            <span className="truncate">{selectedConv.nombre}</span>
                            <span className="text-[11px] sm:text-xs font-normal text-muted font-mono shrink-0">({selectedConv.telefono})</span>
                          </h3>
                          <div className="flex items-center gap-2 text-xs">
                            {selectedConv.estado === 'ESPERANDO_HUMANO' ? (
                              <span className="text-rose-600 font-semibold flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                                IA Pausada (Atendiendo la dueña)
                              </span>
                            ) : (
                              <span className="text-emerald-600 font-semibold flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                                Asistente IA Activa ✦
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Acciones del Chat */}
                      <div className="flex items-center gap-2 shrink-0">
                        {/* Botón Copiar Chat para soporte o análisis rápido */}
                        <button
                          type="button"
                          onClick={handleCopiarChat}
                          className="px-2.5 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-700 hover:text-primary-main hover:border-primary-main/40 hover:bg-slate-50 transition-all flex items-center gap-1.5 text-xs font-bold shadow-2xs"
                          title="Copiar toda la conversación al portapapeles para pegarla donde quieras"
                        >
                          <Copy className="w-3.5 h-3.5 text-primary-main" />
                          <span className="hidden sm:inline">Copiar Chat</span>
                        </button>

                        {/* Botón Exportar archivo .txt */}
                        <button
                          type="button"
                          onClick={handleDescargarChat}
                          className="p-1.5 rounded-xl border border-slate-200 bg-white text-slate-700 hover:text-emerald-700 hover:border-emerald-300 hover:bg-emerald-50/50 transition-all flex items-center gap-1 text-xs font-bold shadow-2xs"
                          title="Descargar conversación en archivo de texto (.txt)"
                        >
                          <Download className="w-3.5 h-3.5 text-emerald-600" />
                        </button>

                        <button
                          onClick={handleTogglePausa}
                          disabled={isTogglingPausa}
                          className={`text-xs font-bold px-3 py-1.5 rounded-xl transition-all flex items-center gap-1.5 border shadow-2xs ${
                            selectedConv.estado === 'ESPERANDO_HUMANO'
                              ? 'bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border-emerald-300'
                              : 'bg-amber-50 hover:bg-amber-100 text-amber-900 border-amber-300'
                          }`}
                          title={selectedConv.estado === 'ESPERANDO_HUMANO' ? 'Reanudar respuesta automática' : 'Pausar IA para hablarle vos directamente'}
                        >
                          {selectedConv.estado === 'ESPERANDO_HUMANO' ? (
                            <>
                              <PlayCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                              <span className="hidden sm:inline">Reanudar IA</span>
                              <span className="sm:hidden">Reanudar</span>
                            </>
                          ) : (
                            <>
                              <PauseCircle className="w-4 h-4 text-amber-600 shrink-0" />
                              <span className="hidden sm:inline">Pausar IA / Atender yo</span>
                              <span className="sm:hidden">Pausar</span>
                            </>
                          )}
                        </button>

                        <button
                          onClick={() => fetchMensajesData(selectedConv.id)}
                          className="p-1.5 rounded-xl border border-slate-200 text-slate-500 hover:text-primary-main hover:bg-slate-50 transition-colors"
                          title="Actualizar mensajes"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Mensajes Container */}
                    <div 
                      ref={chatContainerRef}
                      onScroll={handleChatScroll}
                      className="flex-1 p-4 overflow-y-auto space-y-3 custom-scrollbar relative"
                    >
                      {loadingMsgs ? (
                        <div className="p-8 text-center text-xs text-muted">
                          <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-primary-main" />
                          Cargando mensajes...
                        </div>
                      ) : mensajes.length === 0 ? (
                        <div className="p-8 text-center text-xs text-muted">
                          No hay mensajes en esta conversación.
                        </div>
                      ) : (
                        mensajes.map((msg) => {
                          const isCliente = msg.direccion === 'ENTRANTE';
                          const isHumano = msg.agente_responsable === 'humano_admin';

                          return (
                            <div
                              key={msg.id}
                              className={`flex flex-col ${isCliente ? 'items-start' : 'items-end'}`}
                            >
                              <div
                                className={`max-w-[85%] sm:max-w-[70%] p-3.5 rounded-2xl shadow-2xs text-xs leading-relaxed ${
                                  isCliente
                                    ? 'bg-white text-slate-800 rounded-tl-xs border border-slate-200'
                                    : isHumano
                                    ? 'bg-indigo-600 text-white rounded-tr-xs shadow-sm'
                                    : 'bg-primary-main text-white rounded-tr-xs shadow-sm'
                                }`}
                              >
                                {/* Encabezado de la burbuja */}
                                <div className="flex items-center justify-between gap-3 mb-1 opacity-80 text-[10px] font-semibold">
                                  <span>
                                    {isCliente ? (
                                      'Clienta'
                                    ) : isHumano ? (
                                      '👤 Administradora (Manual)'
                                    ) : (
                                      `✦ IA (${msg.agente_responsable || 'Asistente'})`
                                    )}
                                  </span>
                                  <span>{msg.created_at}</span>
                                </div>

                                {/* Texto del mensaje */}
                                <p className="whitespace-pre-wrap">{msg.texto}</p>

                                {/* Badges de tools ejecutadas por la IA */}
                                {msg.tools_ejecutadas && msg.tools_ejecutadas.length > 0 && (
                                  <div className="mt-2 pt-2 border-t border-white/20 flex flex-wrap gap-1">
                                    {msg.tools_ejecutadas.map((tool, idx) => (
                                      <span
                                        key={idx}
                                        className="text-[9px] font-mono bg-black/20 text-white/95 px-1.5 py-0.5 rounded"
                                      >
                                        ⚡ {tool}
                                      </span>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        })
                      )}
                      {showScrollBottomBtn && (
                        <button
                          type="button"
                          onClick={() => scrollToBottom(true)}
                          className="sticky bottom-3 float-right mr-2 bg-slate-900/90 text-white px-3 py-1.5 rounded-full text-xs font-bold shadow-lg hover:bg-slate-900 transition-all flex items-center gap-1.5 z-20 backdrop-blur-xs border border-white/20 animate-fade-in cursor-pointer"
                          title="Ir a los mensajes más recientes"
                        >
                          <ChevronDown className="w-3.5 h-3.5" />
                          <span>Ir al final</span>
                        </button>
                      )}
                      <div ref={messagesEndRef} />
                    </div>

                    {/* Barra de Entrada de Mensaje */}
                    <form onSubmit={handleEnviarMensaje} className="p-2.5 sm:p-3 bg-white border-t border-slate-200 flex gap-2">
                      <input
                        type="text"
                        placeholder="Escribir mensaje a esta clienta..."
                        value={nuevoMensajeTexto}
                        onChange={(e) => setNuevoMensajeTexto(e.target.value)}
                        disabled={isSendingMsg}
                        className="flex-1 p-2.5 rounded-xl border border-primary-light text-base sm:text-xs focus:outline-none focus:ring-2 focus:ring-primary-main bg-white"
                      />
                      <Button
                        type="submit"
                        disabled={isSendingMsg || !nuevoMensajeTexto.trim()}
                        className="bg-primary-main hover:bg-primary-dark text-white px-3 sm:px-4 shrink-0 text-xs font-bold"
                      >
                        <Send className="w-3.5 h-3.5 sm:mr-1" />
                        <span className="hidden sm:inline">{isSendingMsg ? 'Enviando...' : 'Enviar'}</span>
                      </Button>
                    </form>
                  </>
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-muted">
                    <MessageSquare className="w-12 h-12 text-primary-light mb-3" />
                    <h3 className="text-base font-bold text-foreground mb-1">Monitor de WhatsApp CRM</h3>
                    <p className="text-xs max-w-sm">
                      Seleccioná una conversación del panel izquierdo para auditar la charla en tiempo real o intervenir manualmente.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ======================================================== */}
      {/* PESTAÑA 2: HISTORIAL DE EMAILS                          */}
      {/* ======================================================== */}
      {activeTab === 'emails' && (
        <Card className="border-primary-light/50">
          <CardContent className="p-5 space-y-4">
            
            {/* Filtros de Búsqueda de Emails */}
            <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
              <form onSubmit={handleSearchEmailSubmit} className="relative w-full sm:w-80">
                <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted" />
                <input
                  type="text"
                  placeholder="Buscar por email o asunto..."
                  value={searchEmail}
                  onChange={(e) => setSearchEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-xs rounded-xl border border-primary-light focus:outline-none focus:ring-2 focus:ring-primary-main bg-white"
                />
              </form>

              <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                <select
                  value={estadoEmailFilter}
                  onChange={(e) => {
                    setEstadoEmailFilter(e.target.value);
                  }}
                  className="p-2 rounded-xl border border-primary-light text-xs bg-white text-foreground focus:outline-none focus:ring-2 focus:ring-primary-main"
                >
                  <option value="">Todos los Estados</option>
                  <option value="ENVIADO">✓ Enviados</option>
                  <option value="FALLIDO">✕ Fallidos</option>
                </select>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={fetchEmailLogsData}
                  className="text-xs font-semibold"
                >
                  <RefreshCw className={`w-3.5 h-3.5 mr-1 ${loadingEmails ? 'animate-spin' : ''}`} />
                  Actualizar
                </Button>
              </div>
            </div>

            {/* Tabla de Emails */}
            <div className="overflow-x-auto rounded-xl border border-slate-200">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200 uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="p-3">Destinatario</th>
                    <th className="p-3">Asunto</th>
                    <th className="p-3">Plantilla</th>
                    <th className="p-3">Fecha y Hora</th>
                    <th className="p-3 text-center">Estado</th>
                    <th className="p-3 text-right">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {loadingEmails ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-muted">
                        <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-primary-main" />
                        Cargando registro de correos...
                      </td>
                    </tr>
                  ) : emailLogs.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="p-8 text-center text-muted">
                        No hay correos registrados con los filtros seleccionados.
                      </td>
                    </tr>
                  ) : (
                    emailLogs.map((log) => (
                      <tr key={log.id} className="hover:bg-slate-50/80 transition-colors">
                        <td className="p-3 font-medium text-foreground">{log.destinatario}</td>
                        <td className="p-3 font-semibold text-primary-main">{log.asunto}</td>
                        <td className="p-3 text-muted font-mono text-[11px]">{log.template_name || 'simple'}</td>
                        <td className="p-3 text-slate-600">{log.created_at}</td>
                        <td className="p-3 text-center">
                          {log.estado === 'ENVIADO' ? (
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 inline-flex items-center gap-1">
                              <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Enviado
                            </span>
                          ) : (
                            <span 
                              className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-rose-50 text-rose-700 border border-rose-200 inline-flex items-center gap-1 cursor-pointer"
                              title={log.error_mensaje}
                            >
                              <AlertCircle className="w-3 h-3 text-rose-600" /> Fallido
                            </span>
                          )}
                        </td>
                        <td className="p-3 text-right">
                          <button
                            onClick={() => handleVerEmail(log.id)}
                            className="text-[11px] font-semibold text-primary-main hover:text-primary-dark hover:underline inline-flex items-center gap-1"
                          >
                            <Eye className="w-3.5 h-3.5" /> Ver Correo
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

          </CardContent>
        </Card>
      )}

      {/* ======================================================== */}
      {/* PESTAÑA 3: DIAGNÓSTICO Y ERRORES IA (AGENT CENTINELA)    */}
      {/* ======================================================== */}
      {activeTab === 'errores' && (
        <Card className="border-slate-200 overflow-hidden shadow-sm bg-white">
          <CardContent className="p-4 sm:p-6 space-y-4">
            {/* Header de la pestaña */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-xl bg-slate-900 text-amber-400">
                  <Terminal className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    Bitácora Centinela de Diagnóstico IA
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold">
                      {erroresIA.length} {verResueltos ? 'totales' : 'activos'}
                    </span>
                  </h2>
                  <p className="text-xs text-muted">
                    Monitoreo en tiempo real de fallos técnicos, cuotas de API y diagnóstico comprensible en lenguaje humano.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleExportarErrores}
                  disabled={erroresIA.length === 0}
                  className="px-3 py-1.5 rounded-xl text-xs font-bold border border-slate-200 text-slate-700 bg-white hover:bg-slate-50 flex items-center gap-1.5 transition-all shadow-sm disabled:opacity-50"
                  title="Descargar reporte completo de errores"
                >
                  <Download className="w-3.5 h-3.5 text-primary-main" />
                  <span>Exportar / Descargar</span>
                </button>

                {!verResueltos && erroresIA.length > 0 && (
                  <button
                    type="button"
                    onClick={handleResolverTodos}
                    className="px-3 py-1.5 rounded-xl text-xs font-bold border border-emerald-300 text-emerald-800 bg-emerald-50 hover:bg-emerald-100 flex items-center gap-1.5 transition-all shadow-sm"
                    title="Marcar todos los errores activos como resueltos"
                  >
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Resolver todos ({erroresIA.length})</span>
                  </button>
                )}

                <button
                  type="button"
                  onClick={() => setVerResueltos(!verResueltos)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                    verResueltos
                      ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                      : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  {verResueltos ? '✓ Mostrando resueltos' : 'Ver resueltos'}
                </button>
                <button
                  type="button"
                  onClick={fetchErroresData}
                  disabled={loadingErrores}
                  className="p-2 rounded-xl border border-slate-200 text-slate-600 hover:bg-slate-50 transition-all"
                  title="Recargar"
                >
                  <RefreshCw className={`w-4 h-4 ${loadingErrores ? 'animate-spin text-primary-main' : ''}`} />
                </button>
              </div>
            </div>

            {/* Listado de Errores */}
            {loadingErrores ? (
              <div className="p-12 text-center text-xs text-muted">
                <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-primary-main" />
                Consultando bitácora del agente centinela...
              </div>
            ) : erroresIA.length === 0 ? (
              <div className="p-12 text-center bg-emerald-50/60 rounded-2xl border border-emerald-100 space-y-2">
                <ShieldCheck className="w-8 h-8 text-emerald-600 mx-auto" />
                <h3 className="text-sm font-bold text-emerald-900">
                  {verResueltos ? 'No hay errores resueltos para mostrar' : '¡Todo el sistema de IA está funcionando a la perfección!'}
                </h3>
                <p className="text-xs text-emerald-700 max-w-md mx-auto">
                  {verResueltos
                    ? 'No se encontraron tickets resueltos en el historial.'
                    : 'No hay errores pendientes ni interrupciones registradas en las conversaciones de WhatsApp.'}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {erroresIA.map((item) => {
                  const isExpanded = expandedErrorId === item.id;
                  return (
                    <div
                      key={item.id}
                      className={`border rounded-2xl p-4 transition-all ${
                        item.resuelto
                          ? 'bg-slate-50/60 border-slate-200 opacity-75'
                          : 'bg-white border-rose-200 shadow-sm'
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-100">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-900 text-white">
                            {item.ticket}
                          </span>
                          <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                            item.rol_usuario === 'DUENA'
                              ? 'bg-purple-100 text-purple-800 border border-purple-200'
                              : 'bg-slate-100 text-slate-700'
                          }`}>
                            {item.rol_usuario} {item.telefono ? `(${item.telefono})` : ''}
                          </span>
                          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                            {item.tipo_error}
                          </span>
                          <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                            Agente: {item.agente_responsable}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted">
                          <Clock className="w-3.5 h-3.5" />
                          <span>{item.created_at}</span>
                        </div>
                      </div>

                      {/* Mensaje que provocó el error */}
                      {item.mensaje_usuario && (
                        <div className="mt-2.5 text-xs text-slate-700 bg-slate-50 p-2.5 rounded-xl border border-slate-100">
                          <span className="font-bold text-slate-900">Mensaje recibido: </span>
                          <span className="italic">"{item.mensaje_usuario}"</span>
                        </div>
                      )}

                      {/* Diagnóstico en Lenguaje Humano */}
                      <div className="mt-3 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200/80 p-3 rounded-xl text-xs space-y-1">
                        <div className="flex items-center gap-1.5 font-bold text-amber-900">
                          <Sparkles className="w-4 h-4 text-amber-600" />
                          <span>Diagnóstico Inteligente:</span>
                        </div>
                        <p className="text-amber-950 leading-relaxed font-sans">
                          {item.diagnostico_ia || 'Inconveniente detectado durante el procesamiento.'}
                        </p>
                      </div>

                      {/* Detalle técnico */}
                      <div className="mt-2 text-xs font-mono bg-slate-900 text-slate-200 p-2.5 rounded-xl overflow-x-auto">
                        <span className="text-rose-400 font-bold">Error: </span>
                        <span>{item.detalle_error}</span>
                      </div>

                      {/* Acciones y Stack trace */}
                      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 text-xs">
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => setExpandedErrorId(isExpanded ? null : item.id)}
                            className="text-slate-600 hover:text-slate-900 inline-flex items-center gap-1 font-semibold"
                          >
                            <Terminal className="w-3.5 h-3.5" />
                            <span>{isExpanded ? 'Ocultar consola / traceback' : 'Ver consola / traceback'}</span>
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>

                          <button
                            type="button"
                            onClick={() => {
                              const textoError = `[ERROR IA ${item.ticket}]\nFecha: ${item.created_at}\nRol: ${item.rol_usuario} (${item.telefono || 'Sin tel'})\nAgente: ${item.agente_responsable}\nTipo: ${item.tipo_error}\nMensaje: "${item.mensaje_usuario || ''}"\nDiagnóstico: ${item.diagnostico_ia || ''}\nError: ${item.detalle_error}\nTraceback: ${item.traceback_completo || 'N/A'}`;
                              navigator.clipboard?.writeText(textoError);
                              toast.success('¡Detalle del error copiado al portapapeles!');
                            }}
                            className="text-slate-500 hover:text-slate-800 inline-flex items-center gap-1 font-medium"
                            title="Copiar este error para compartir"
                          >
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copiar error</span>
                          </button>
                        </div>

                        <button
                          type="button"
                          onClick={() => handleToggleResolver(item.id)}
                          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold transition-all ${
                            item.resuelto
                              ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                              : 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-sm'
                          }`}
                        >
                          <CheckCircle className="w-3.5 h-3.5" />
                          <span>{item.resuelto ? 'Reabrir ticket' : 'Marcar como resuelto'}</span>
                        </button>
                      </div>

                      {/* Stack Trace desplegable */}
                      {isExpanded && item.traceback_completo && (
                        <div className="mt-3 p-3 bg-black/95 rounded-xl text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-64 whitespace-pre">
                          {item.traceback_completo}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Modal Vista Previa de Correo */}
      <Modal
        isOpen={isEmailModalOpen}
        onClose={() => setIsEmailModalOpen(false)}
        title={selectedEmailDetail ? `Vista Previa: ${selectedEmailDetail.asunto}` : "Cargando correo..."}
      >
        {loadingEmailDetail || !selectedEmailDetail ? (
          <div className="p-8 text-center text-xs text-muted">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-primary-main" />
            Cargando contenido del correo...
          </div>
        ) : (
          <div className="space-y-4 text-left">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-xs space-y-1">
              <p><strong>Destinatario:</strong> {selectedEmailDetail.destinatario}</p>
              <p><strong>Asunto:</strong> {selectedEmailDetail.asunto}</p>
              <p><strong>Fecha:</strong> {selectedEmailDetail.created_at}</p>
              <p>
                <strong>Estado:</strong>{' '}
                <span className={selectedEmailDetail.estado === 'ENVIADO' ? 'text-emerald-700 font-bold' : 'text-rose-700 font-bold'}>
                  {selectedEmailDetail.estado}
                </span>
                {selectedEmailDetail.error_mensaje && (
                  <span className="block text-rose-600 text-[11px] mt-1">Error: {selectedEmailDetail.error_mensaje}</span>
                )}
              </p>
            </div>

            {/* Visualización del contenido */}
            <div className="border border-slate-200 rounded-xl overflow-hidden bg-white">
              {selectedEmailDetail.cuerpo_html ? (
                <iframe
                  title="Email Preview"
                  srcDoc={selectedEmailDetail.cuerpo_html}
                  className="w-full h-96 border-0"
                />
              ) : (
                <div className="p-4 text-xs whitespace-pre-wrap font-sans text-slate-800">
                  {selectedEmailDetail.cuerpo_texto || 'Sin contenido de texto registrado.'}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="outline" onClick={() => setIsEmailModalOpen(false)}>
                Cerrar
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </motion.div>
  );
}
