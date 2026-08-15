/* Developed by FireSeed - Fueling Innovation */
import React, { useState } from 'react'
import { useClientProfile } from '../hooks/useClientProfile'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Badge } from '../components/ui/Badge'
import { BookingGrid } from '../components/booking/BookingGrid'
import { CancelModal } from '../components/booking/CancelModal'
import { useBookings, type Turno } from '../hooks/useBookings'
import { api } from '../lib/api'

const formatUpcomingDate = (dateStr: string) => {
  const [year, month, day] = dateStr.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  const weekdayFormatter = new Intl.DateTimeFormat('es-AR', { weekday: 'long' })
  const weekday = weekdayFormatter.format(date)
  const capitalizedWeekday = weekday.charAt(0).toUpperCase() + weekday.slice(1)
  
  const monthFormatter = new Intl.DateTimeFormat('es-AR', { month: 'short' })
  const monthShort = monthFormatter.format(date).replace('.', '')
  const capitalizedMonth = monthShort.charAt(0).toUpperCase() + monthShort.slice(1)
  
  const paddedDay = String(day).padStart(2, '0')
  return `${capitalizedWeekday} ${paddedDay} ${capitalizedMonth}`
}

const formatExpirationDate = (dateStr: string) => {
  if (!dateStr) return ''
  const [year, month, day] = dateStr.split('-')
  return `${day}-${month}-${year}`
}

export function Dashboard() {
  const { profile, loading: profileLoading, refetch: refetchProfile } = useClientProfile()
  const { turnos, loading: bookingsLoading, bookTurno, cancelTurno, refetch: refetchTurnos } = useBookings()
  const [selectedTurnoToCancel, setSelectedTurnoToCancel] = useState<Turno | null>(null)

  const handleBook = async (id: string, recurring: boolean) => {
    await bookTurno(id, recurring)
    refetchProfile()
  }

  const handleCancel = async (id: string) => {
    await cancelTurno(id)
    refetchProfile()
    setSelectedTurnoToCancel(null)
  }

  const handleCancelRecurrencia = async (id: string) => {
    if (!window.confirm('¿Estás seguro de cancelar tu horario fijo permanentemente? Esto cancelará todas tus reservas futuras para este horario.')) return
    try {
      await api.post('/recurrencias/cancel/', { id })
      refetchProfile()
      refetchTurnos()
    } catch (err: any) {
      alert("Error al cancelar el horario fijo.")
    }
  }

  if (profileLoading || bookingsLoading) {
    return <div className="min-h-screen flex items-center justify-center text-violett-900">Cargando perfil...</div>
  }

  if (!profile) return null

  const myUpcomingBookings = turnos.filter(t => t.isBookedByMe)

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Header Profile */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Hola, {profile.name}</h1>
          <p className="text-muted mt-1">Bienvenida de nuevo a Violett Pilates.</p>
        </div>
        <Badge variant={profile.daysUntilExpiration < 7 ? "destructive" : "secondary"} className="text-sm px-4 py-1">
          Vence en {profile.daysUntilExpiration} días
        </Badge>
      </div>

      {/* Plan Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-gradient-to-br from-violett-900 to-violett-700 text-white border-none shadow-glass">
          <CardHeader>
            <CardTitle className="text-white/90 text-lg">Mi Plan Actual</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{profile.activePlan}</p>
            <p className="text-violett-200 mt-2 text-sm">Válido hasta el {formatExpirationDate(profile.expirationDate)}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg text-muted">Clases Disponibles</CardTitle>
          </CardHeader>
          <CardContent className="flex items-baseline gap-2">
            <span className="text-4xl font-bold text-violett-900">{profile.remainingClasses}</span>
            <span className="text-muted font-medium">de {profile.totalClasses}</span>
          </CardContent>
        </Card>
      </div>

      {/* Mi Horario Fijo */}
      {profile.recurrencias && profile.recurrencias.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground">Mi Horario Fijo / Recurrente</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profile.recurrencias.map(rec => {
              const days = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábados', 'Domingos']
              const dayName = days[rec.dia_semana - 1]
              return (
                <Card key={rec.id} className="border-l-4 border-l-violett-700 bg-violett-50/50">
                  <CardHeader className="pb-2">
                    <div className="flex justify-between items-center">
                      <Badge variant="secondary">Fijo Semanal</Badge>
                      <button 
                        onClick={() => handleCancelRecurrencia(rec.id)}
                        className="text-sm font-medium text-red-500 hover:text-red-700 transition-colors"
                      >
                        Baja definitiva
                      </button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-xl font-bold text-foreground mb-1">{rec.classType}</p>
                    <p className="text-muted text-sm">Todos los {dayName}</p>
                    <p className="text-muted text-sm font-medium">• {rec.time} hs</p>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}

      {/* Mis Próximas Clases Confirmadas */}
      {myUpcomingBookings.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground">Mis Próximas Clases Confirmadas</h2>
          <div className="flex gap-3 overflow-x-auto pb-4 snap-x">
            {myUpcomingBookings.map(turno => (
              <Card key={turno.id} className="min-w-[280px] snap-start border-l-4 border-l-violett-500">
                <CardHeader className="pb-2">
                  <Badge className="w-fit" variant={turno.isRecurring ? "secondary" : "default"}>
                    {turno.isRecurring ? "Clase fija" : "Puntual"}
                  </Badge>
                </CardHeader>
                <CardContent>
                  <div className="flex justify-between items-end">
                    <div>
                      <p className="text-xl font-bold text-foreground mb-1">{turno.classType}</p>
                      <p className="text-muted text-sm">{formatUpcomingDate(turno.date)}</p>
                      <p className="text-muted text-sm font-medium">• {turno.time} hs</p>
                    </div>
                    <button 
                      onClick={() => setSelectedTurnoToCancel(turno)}
                      className="text-sm font-medium text-red-500 hover:text-red-700 transition-colors"
                    >
                      Cancelar
                    </button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Grilla de Reservas */}
      <div className="pt-4 border-t border-violett-100">
        <BookingGrid 
          turnos={turnos}
          loading={bookingsLoading}
          onBook={handleBook}
          onCancel={handleCancel}
        />
      </div>

      <CancelModal 
        isOpen={!!selectedTurnoToCancel}
        onClose={() => setSelectedTurnoToCancel(null)}
        turno={selectedTurnoToCancel}
        onConfirm={handleCancel}
      />

    </div>
  )
}
