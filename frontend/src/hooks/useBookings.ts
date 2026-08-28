/* Developed by FireSeed - Fueling Innovation */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'
import { toast } from 'sonner'

export interface Turno {
  id: string
  date: string // ISO date
  time: string // HH:mm
  classType: string
  availableSpots: number
  totalSpots: number
  isBookedByMe: boolean
  isRecurring: boolean
  allowsRecurring: boolean
}

export function useBookings() {
  const queryClient = useQueryClient()

  const { data: turnos = [], isLoading: loading, error: queryError, refetch } = useQuery<Turno[]>({
    queryKey: ['turnos'],
    queryFn: async () => {
      const response = await api.get('/turnos/')
      return response.data
    }
  })

  const bookMutation = useMutation({
    mutationFn: async ({ turnoId, recurring }: { turnoId: string, recurring: boolean }) => {
      await api.post('/reservas/book/', { turno_id: turnoId, is_recurring: recurring })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['turnos'] })
      queryClient.invalidateQueries({ queryKey: ['clientProfile'] }) // also refresh available spots
      toast.success('¡Clase reservada con éxito!')
    },
    onError: (err: any) => {
      console.error('Error booking turno:', err)
      toast.error(err.response?.data?.detail || "No se pudo reservar el turno.")
    }
  })

  const cancelMutation = useMutation({
    mutationFn: async (turnoId: string) => {
      await api.post('/reservas/cancel/', { turno_id: turnoId })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['turnos'] })
      queryClient.invalidateQueries({ queryKey: ['clientProfile'] })
      toast.success('Clase cancelada.')
    },
    onError: (err: any) => {
      console.error('Error cancelling turno:', err)
      toast.error(err.response?.data?.detail || "No se pudo cancelar el turno.")
    }
  })

  return { 
    turnos, 
    loading, 
    error: queryError ? queryError.message : null, 
    bookTurno: (id: string, rec: boolean) => bookMutation.mutateAsync({ turnoId: id, recurring: rec }), 
    cancelTurno: (id: string) => cancelMutation.mutateAsync(id), 
    refetch 
  }
}
