/* Developed by FireSeed - Fueling Innovation */
import { useState, useEffect, useCallback } from 'react'
import { api } from '../lib/api'

export interface Turno {
  id: string
  date: string // ISO date
  time: string // HH:mm
  classType: string
  availableSpots: number
  totalSpots: number
  isBookedByMe: boolean
  isRecurring: boolean
}

export function useBookings() {
  const [turnos, setTurnos] = useState<Turno[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTurnos = useCallback(async () => {
    try {
      setLoading(true)
      const response = await api.get('/turnos/')
      setTurnos(response.data)
    } catch (err: any) {
      console.error('Error fetching turnos:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTurnos()
  }, [fetchTurnos])

  const bookTurno = async (turnoId: string, recurring: boolean) => {
    try {
      await api.post('/reservas/book/', { turno_id: turnoId, is_recurring: recurring })
      // Re-fetch to get updated state from server
      await fetchTurnos()
    } catch (err: any) {
      console.error('Error booking turno:', err)
      alert(err.response?.data?.detail || "No se pudo reservar el turno.")
    }
  }

  const cancelTurno = async (turnoId: string) => {
    try {
      await api.post('/reservas/cancel/', { turno_id: turnoId })
      // Re-fetch to get updated state from server
      await fetchTurnos()
    } catch (err: any) {
      console.error('Error cancelling turno:', err)
      alert(err.response?.data?.detail || "No se pudo cancelar el turno.")
    }
  }

  return { turnos, loading, error, bookTurno, cancelTurno, refetch: fetchTurnos }
}
