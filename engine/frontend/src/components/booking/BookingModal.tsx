/* Developed by FireSeed - Fueling Innovation */
import React, { useState } from 'react'
import { Modal } from '../ui/Modal'
import { FeedbackButton } from '../ui/FeedbackButton'
import { type Turno } from '../../hooks/useBookings'
import { ArrowRightLeft, Calendar, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../../lib/api'

interface ReservaFutura {
  reserva_id: string
  turno_id: string
  fecha: string
  fecha_formateada: string
  hora: string
  clase_nombre: string
}

interface BookingModalProps {
  isOpen: boolean
  onClose: () => void
  turno: Turno | null
  onConfirm: (turnoId: string, isRecurring: boolean) => Promise<any> | void
  onReprogramar?: (turnoOrigenId: string, turnoDestinoId: string) => Promise<any> | void
}

export function BookingModal({ isOpen, onClose, turno, onConfirm, onReprogramar }: BookingModalProps) {
  const [cachedTurno, setCachedTurno] = useState<Turno | null>(turno)
  const [reprogramarList, setReprogramarList] = useState<ReservaFutura[] | null>(null)
  const [isReprogrammingId, setIsReprogrammingId] = useState<string | null>(null)
  
  React.useEffect(() => {
    if (turno) {
      setCachedTurno(turno)
      setReprogramarList(null)
      setIsReprogrammingId(null)
    }
  }, [turno])

  const displayTurno = turno || cachedTurno

  const handleClose = () => {
    setReprogramarList(null)
    setIsReprogrammingId(null)
    onClose()
  }

  const handleConfirm = async (isRecurring: boolean) => {
    if (!displayTurno) return
    try {
      await onConfirm(displayTurno.id, isRecurring)
      handleClose()
    } catch (err: any) {
      const errData = err.response?.data
      if (errData?.code === 'SIN_CREDITOS_CON_FUTURAS' && Array.isArray(errData.reservas_futuras) && errData.reservas_futuras.length > 0) {
        setReprogramarList(errData.reservas_futuras)
      } else {
        handleClose()
      }
    }
  }

  const handleExecuteReprogramar = async (reservaOrigen: ReservaFutura) => {
    if (!displayTurno) return
    try {
      setIsReprogrammingId(reservaOrigen.turno_id)
      if (onReprogramar) {
        await onReprogramar(reservaOrigen.turno_id, displayTurno.id)
      } else {
        const res = await api.post('/reservas/reprogramar/', {
          turno_origen_id: reservaOrigen.turno_id,
          turno_destino_id: displayTurno.id
        })
        toast.success(res.data?.detail || '¡Clase reprogramada con éxito!')
      }
      handleClose()
    } catch (e: any) {
      console.error(e)
      toast.error(e.response?.data?.detail || 'No se pudo reprogramar la clase.')
    } finally {
      setIsReprogrammingId(null)
    }
  }

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={handleClose} 
      title={reprogramarList ? "Modificar Clase Agendada" : "Confirmar Reserva"}
    >
      {displayTurno ? (
        <div className="space-y-5">
          {/* Tarjeta del turno nuevo solicitado */}
          <div className="rounded-2xl bg-violet-50/80 border border-violet-100 p-4">
            <div className="flex items-center justify-between text-xs font-semibold text-violet-700 mb-1">
              <span>{displayTurno.date} • {displayTurno.time} hs</span>
              <span className="flex items-center gap-1 text-[11px] font-bold bg-violet-200/60 text-violet-800 px-2 py-0.5 rounded-full">
                <Sparkles className="w-3 h-3" /> Nuevo horario
              </span>
            </div>
            <p className="text-base font-bold text-violet-950">{displayTurno.classType}</p>
          </div>

          {reprogramarList ? (
            /* Vista de cambio / reprogramación de clase por falta de créditos */
            <div className="space-y-4">
              <div className="rounded-xl bg-amber-50/90 border border-amber-200/80 p-3.5">
                <div className="flex items-start gap-2.5">
                  <div className="p-1.5 bg-amber-100 text-amber-700 rounded-lg shrink-0 mt-0.5">
                    <ArrowRightLeft className="w-4 h-4" />
                  </div>
                  <div className="text-xs text-amber-900 leading-relaxed">
                    <p className="font-bold text-amber-950">No tenés créditos libres en tu abono</p>
                    <p className="mt-0.5">
                      Podés cambiar una de tus clases ya agendadas a futuro para pasarla a este nuevo horario sin costo extra:
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <p className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">
                  Elegí cuál de tus clases querés mover:
                </p>
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {reprogramarList.map((rf) => (
                    <div
                      key={rf.reserva_id || rf.turno_id}
                      className="flex items-center justify-between p-3 bg-neutral-50 hover:bg-violet-50/50 border border-neutral-200 hover:border-violet-300 rounded-xl transition"
                    >
                      <div className="min-w-0 pr-2">
                        <p className="text-xs font-bold text-neutral-800 flex items-center gap-1.5">
                          <Calendar className="w-3.5 h-3.5 text-neutral-400" />
                          {rf.fecha_formateada} a las {rf.hora} hs
                        </p>
                        <p className="text-[11px] text-neutral-500 truncate mt-0.5">
                          {rf.clase_nombre}
                        </p>
                      </div>
                      <button
                        type="button"
                        disabled={isReprogrammingId !== null}
                        onClick={() => handleExecuteReprogramar(rf)}
                        className="px-3 py-1.5 text-xs font-bold text-white bg-violet-600 hover:bg-violet-700 active:scale-95 disabled:opacity-50 rounded-lg shadow-sm transition shrink-0"
                      >
                        {isReprogrammingId === rf.turno_id ? 'Moviendo...' : 'Mover aquí'}
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="pt-2 border-t border-neutral-100 flex justify-end">
                <button
                  type="button"
                  onClick={() => setReprogramarList(null)}
                  className="text-xs text-neutral-500 hover:text-neutral-800 font-semibold px-3 py-1.5 rounded-lg hover:bg-neutral-100 transition"
                >
                  Volver
                </button>
              </div>
            </div>
          ) : (
            /* Vista de reserva normal */
            <>
              <p className="text-muted text-sm">
                {displayTurno.allowsRecurring 
                  ? '¿Cómo te gustaría reservar este turno? Podés anotarte solo para este día, o fijar este horario todas las semanas.' 
                  : 'Esta clase es puntual. Solo podés reservar para esta fecha específica.'}
              </p>

              <div className="flex flex-col gap-3">
                <FeedbackButton
                  onClick={() => handleConfirm(false)}
                  className="w-full"
                  initialText="Reserva Puntual (Solo esta clase)"
                  successText="¡Reservada!"
                />
                {displayTurno.allowsRecurring && (
                  <FeedbackButton
                    onClick={() => handleConfirm(true)}
                    variant="outline"
                    className="w-full"
                    initialText="Reserva Recurrente (Fijo semanal)"
                    successText="¡Reservada!"
                  />
                )}
              </div>
            </>
          )}
        </div>
      ) : null}
    </Modal>
  )
}
