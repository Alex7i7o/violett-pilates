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
      const response = await api.post('/reservas/book/', { turno_id: turnoId, is_recurring: recurring })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['turnos'] })
      queryClient.invalidateQueries({ queryKey: ['clientProfile'] }) // also refresh available spots
      toast.success('¡Clase reservada con éxito!')
    },
    onError: (err: any) => {
      console.error('Error booking turno:', err)
      if (err.response?.data?.code !== 'SIN_CREDITOS_CON_FUTURAS') {
        toast.error(err.response?.data?.detail || "No se pudo reservar el turno.")
      }
    }
  })

  const reprogramarMutation = useMutation({
    mutationFn: async ({ turnoOrigenId, turnoDestinoId }: { turnoOrigenId: string, turnoDestinoId: string }) => {
      const response = await api.post('/reservas/reprogramar/', {
        turno_origen_id: turnoOrigenId,
        turno_destino_id: turnoDestinoId
      })
      return response.data
    },
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['turnos'] })
      queryClient.invalidateQueries({ queryKey: ['clientProfile'] })
      toast.success(data?.detail || '¡Clase reprogramada con éxito!')
    },
    onError: (err: any) => {
      console.error('Error reprogramando turno:', err)
      toast.error(err.response?.data?.detail || "No se pudo reprogramar la clase.")
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
    reprogramarTurno: (origenId: string, destinoId: string) => reprogramarMutation.mutateAsync({ turnoOrigenId: origenId, turnoDestinoId: destinoId }),
    cancelTurno: (id: string) => cancelMutation.mutateAsync(id), 
    refetch 
  }
}
