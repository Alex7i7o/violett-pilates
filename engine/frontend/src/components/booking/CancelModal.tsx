import React, { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Modal } from '../ui/Modal'
import { Button } from '../ui/Button'
import { FeedbackButton } from '../ui/FeedbackButton'
import { type Turno } from '../../hooks/useBookings'
import { AlertTriangle, Calendar, Sparkles } from 'lucide-react'
import { toast } from 'sonner'

interface CancelModalProps {
  isOpen: boolean
  onClose: () => void
  turno: Turno | null
  onConfirm: (turnoId: string) => Promise<void> | void
}

export function CancelModal({ isOpen, onClose, turno, onConfirm }: CancelModalProps) {
  const navigate = useNavigate()
  const [cachedTurno, setCachedTurno] = React.useState<Turno | null>(turno)
  const [isRescheduling, setIsRescheduling] = React.useState(false)
  
  React.useEffect(() => {
    if (turno) setCachedTurno(turno)
  }, [turno])

  const displayTurno = turno || cachedTurno

  const isLateCancellation = useMemo(() => {
    if (!displayTurno) return false
    const [year, month, day] = displayTurno.date.split('-').map(Number)
    const [hours, minutes] = displayTurno.time.split(':').map(Number)
    const turnoDate = new Date(year, month - 1, day, hours, minutes)
    const now = new Date()
    const diffHours = (turnoDate.getTime() - now.getTime()) / (1000 * 60 * 60)
    return diffHours < 24
  }, [displayTurno])

  const handleReschedule = async () => {
    if (!displayTurno) return
    try {
      setIsRescheduling(true)
      await onConfirm(displayTurno.id)
      onClose()
      toast.success('Clase liberada con éxito. Elegí tu nuevo horario en la agenda 🌸')
      navigate('/')
    } catch (e) {
      toast.error('No se pudo reprogramar la clase.')
    } finally {
      setIsRescheduling(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Gestión de tu Clase">
      {displayTurno ? (
      <div className="space-y-5">
        {/* Detalle de la clase a modificar */}
        <div className="bg-primary-light/40 border border-primary-light rounded-2xl p-4 flex items-center justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-muted font-bold">Clase actual</p>
            <p className="font-bold text-foreground text-base mt-0.5">
              {displayTurno.date} a las {displayTurno.time} hs
            </p>
            <p className="text-xs text-primary-main font-medium">{displayTurno.classType}</p>
          </div>
          <div className="w-10 h-10 rounded-xl bg-primary-main/10 text-primary-main flex items-center justify-center font-bold">
            ✦
          </div>
        </div>

        {/* ALERTA DE CANCELACIÓN TARDÍA */}
        {isLateCancellation && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 flex items-start gap-3 text-amber-900">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-amber-600" />
            <div className="text-xs leading-relaxed">
              <p className="font-bold text-sm text-amber-950 mb-0.5">Aviso de tiempo límite (menos de 24 hs)</p>
              Estás modificando tu clase con menos de 24 horas de anticipación. Según nuestra política de convivencia, el crédito no podrá ser devuelto al plan si cancelás.
            </div>
          </div>
        )}

        {/* OPCIÓN RECOMENDADA: REPROGRAMAR */}
        <div className="bg-gradient-to-br from-violett-50 to-white border border-violett-200/80 rounded-2xl p-4 space-y-2">
          <div className="flex items-center gap-2 text-violett-800 font-bold text-xs uppercase tracking-wider">
            <Sparkles className="w-3.5 h-3.5 text-violett-600" />
            <span>Recomendado: No pierdas tu ritmo</span>
          </div>
          <p className="text-xs text-neutral-600 leading-relaxed">
            Podés <strong>reprogramar para otro día y horario</strong> en un solo paso: liberamos esta camilla de inmediato y elegís tu nuevo turno en la agenda.
          </p>
          <Button 
            onClick={handleReschedule} 
            disabled={isRescheduling}
            className="w-full bg-primary-main hover:bg-violett-700 text-white font-bold py-2.5 rounded-xl text-xs sm:text-sm shadow-sm flex items-center justify-center gap-2 mt-2"
          >
            <Calendar className="w-4 h-4" />
            <span>{isRescheduling ? 'Liberando...' : 'Reprogramar para otro día 📅'}</span>
          </Button>
        </div>

        {/* OPCIÓN SECUNDARIA: CANCELAR DEFINITIVA */}
        <div className="pt-2 border-t border-neutral-100 flex flex-col sm:flex-row gap-2 justify-end">
          <Button onClick={onClose} variant="outline" size="sm" className="w-full sm:w-auto text-xs">
            Mantener mi clase
          </Button>
          <FeedbackButton 
            onClick={async () => await onConfirm(displayTurno.id)} 
            variant="destructive" 
            size="sm"
            className="w-full sm:w-auto text-xs" 
            initialText="Solo cancelar y liberar crédito" 
            successText="Cancelada" 
          />
        </div>
      </div>
      ) : null}
    </Modal>
  )
}
