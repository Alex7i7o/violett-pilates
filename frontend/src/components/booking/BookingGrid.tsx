/* Developed by FireSeed - Fueling Innovation */
import React, { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { type Turno } from '../../hooks/useBookings'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { BookingModal } from './BookingModal'
import { CancelModal } from './CancelModal'

// Helper for friendly date
const formatDate = (dateString: string) => {
  const [year, month, day] = dateString.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  
  return new Intl.DateTimeFormat('es-AR', { 
    weekday: 'long', 
    day: 'numeric',
    month: 'long'
  }).format(date).replace(/^\w/, (c) => c.toUpperCase())
}

const formatTabDate = (dateString: string) => {
  const [year, month, day] = dateString.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  
  return new Intl.DateTimeFormat('es-AR', { 
    weekday: 'short', 
    day: 'numeric'
  }).format(date).replace(/^\w/, (c) => c.toUpperCase())
}

export function BookingGrid({
  turnos,
  loading,
  onBook,
  onCancel
}: {
  turnos: Turno[],
  loading: boolean,
  onBook: (id: string, recurring: boolean) => void,
  onCancel: (id: string) => void
}) {
  const [selectedTurnoToBook, setSelectedTurnoToBook] = useState<Turno | null>(null)
  const [selectedTurnoToCancel, setSelectedTurnoToCancel] = useState<Turno | null>(null)
  const [activeDate, setActiveDate] = useState<string>('')

  // Group by date
  const groupedTurnos = useMemo(() => {
    const groups: Record<string, Turno[]> = {}
    turnos.forEach(turno => {
      if (!groups[turno.date]) {
        groups[turno.date] = []
      }
      groups[turno.date].push(turno)
    })
    
    // Sort each group by time
    Object.keys(groups).forEach(date => {
      groups[date].sort((a, b) => a.time.localeCompare(b.time))
    })
    
    return groups
  }, [turnos])

  const availableDates = Object.keys(groupedTurnos).sort()

  // Auto-select first date if activeDate is empty or not in availableDates
  React.useEffect(() => {
    if (availableDates.length > 0 && (!activeDate || !availableDates.includes(activeDate))) {
      setActiveDate(availableDates[0])
    }
  }, [availableDates, activeDate])

  if (loading) {
    return (
      <div className="space-y-4">
        {[1, 2, 3].map(i => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    )
  }

  const handleConfirmBook = (id: string, isRecurring: boolean) => {
    onBook(id, isRecurring)
    setSelectedTurnoToBook(null)
  }

  const handleConfirmCancel = (id: string) => {
    onCancel(id)
    setSelectedTurnoToCancel(null)
  }

  const displayedTurnos = activeDate ? (groupedTurnos[activeDate] || []) : []

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-violett-900">Agenda Disponible</h2>
      
      {/* Tabs */}
      {availableDates.length > 0 && (
        <div className="flex overflow-x-auto gap-2 pb-2 scrollbar-hide snap-x">
          {availableDates.map(date => {
            const dayTurnos = groupedTurnos[date]
            const availableSpots = dayTurnos.reduce((acc, t) => acc + (t.isBookedByMe ? 0 : t.availableSpots), 0)
            const isActive = activeDate === date
            
            return (
              <button
                key={date}
                onClick={() => setActiveDate(date)}
                className={`snap-start relative flex flex-col items-center justify-center min-w-[100px] px-4 py-3 rounded-2xl transition-colors duration-200 z-10 ${
                  isActive 
                    ? 'text-white' 
                    : 'bg-white text-muted hover:bg-violett-50'
                }`}
              >
                {isActive && (
                  <motion.div 
                    layoutId="activeDateTabPill"
                    className="absolute inset-0 bg-violett-900 rounded-2xl shadow-lg"
                    style={{ zIndex: -1 }}
                    transition={{ type: "spring", bounce: 0.15, duration: 0.5 }}
                  />
                )}
                
                <span className="font-semibold">{formatTabDate(date)}</span>
                <span className={`text-xs mt-1 px-2 py-0.5 rounded-full transition-colors duration-200 ${
                  isActive ? 'bg-white/20 text-white' : availableSpots > 0 ? 'bg-violett-100 text-violett-900' : 'bg-red-100 text-red-900'
                }`}>
                  {availableSpots > 0 ? `${availableSpots} cupos` : 'Agotado'}
                </span>
              </button>
            )
          })}
        </div>
      )}

      {/* Grid */}
      <div className="min-h-[300px]">
        <AnimatePresence mode="popLayout">
          {displayedTurnos.length > 0 ? (
            <motion.div 
              key={activeDate}
              variants={{
                hidden: { opacity: 0 },
                show: {
                  opacity: 1,
                  transition: { staggerChildren: 0.05 }
                },
                exit: { opacity: 0, y: -10, transition: { duration: 0.15, ease: "easeOut" } }
              }}
              initial="hidden"
              animate="show"
              exit="exit"
              className="grid gap-4 md:grid-cols-2 lg:grid-cols-3"
            >
              <div className="col-span-full mb-2">
                <h3 className="text-lg font-medium text-foreground capitalize">
                  {formatDate(activeDate)}
                </h3>
              </div>
              
              {displayedTurnos.map((turno) => (
                <motion.div key={turno.id} variants={{ hidden: { opacity: 0, y: 15 }, show: { opacity: 1, y: 0, transition: { type: "spring", duration: 0.4, bounce: 0.1 } } }}>
                <Card className={`transition-all hover:shadow-md ${turno.isBookedByMe ? "border-violett-400 bg-violett-50/30" : ""}`}>
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-xl">{turno.time}</CardTitle>
                        <p className="text-sm font-medium text-violett-600 mt-1">{turno.classType}</p>
                      </div>
                      {turno.isBookedByMe && <Badge variant="secondary">Mi Reserva</Badge>}
                      {!turno.isBookedByMe && turno.availableSpots === 0 && <Badge variant="destructive">Lleno</Badge>}
                      {!turno.isBookedByMe && turno.availableSpots > 0 && (
                        turno.allowsRecurring 
                          ? <Badge variant="secondary" className="bg-violett-100 text-violett-800">Clase fija</Badge> 
                          : <Badge variant="outline" className="border-gray-300 text-gray-500">Puntual</Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between mt-4">
                      <span className="text-sm text-muted">
                        Cupos: {turno.availableSpots} / {turno.totalSpots}
                      </span>
                      
                      {turno.isBookedByMe ? (
                        <Button variant="outline" size="sm" onClick={() => setSelectedTurnoToCancel(turno)}>
                          Cancelar
                        </Button>
                      ) : (
                        <Button 
                          size="sm" 
                          disabled={turno.availableSpots === 0}
                          onClick={() => setSelectedTurnoToBook(turno)}
                        >
                          Agendar
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
                </motion.div>
              ))}
            </motion.div>
          ) : (
            <motion.div 
              key="empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-12 text-muted"
            >
              No hay turnos disponibles para este día.
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <BookingModal 
        isOpen={!!selectedTurnoToBook} 
        onClose={() => setSelectedTurnoToBook(null)}
        turno={selectedTurnoToBook}
        onConfirm={handleConfirmBook}
      />

      <CancelModal 
        isOpen={!!selectedTurnoToCancel}
        onClose={() => setSelectedTurnoToCancel(null)}
        turno={selectedTurnoToCancel}
        onConfirm={handleConfirmCancel}
      />
    </div>
  )
}
