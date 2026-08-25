/* Developed by FireSeed - Fueling Innovation */
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export interface Recurrencia {
  id: string;
  dia_semana: number;
  time: string;
  classType: string;
  is_active: boolean;
}

export interface ClientProfile {
  name: string
  rol: string
  activePlan: string
  remainingClasses: number
  totalClasses: number
  expirationDate: string
  daysUntilExpiration: number
  recurrencias: Recurrencia[]
}

export function useClientProfile() {
  const { data: profile = null, isLoading: loading, error: queryError, refetch } = useQuery<ClientProfile>({
    queryKey: ['clientProfile'],
    queryFn: async () => {
      const response = await api.get('/profile/')
      return response.data
    },
    retry: false, // Don't retry on 401
  })

  return { 
    profile, 
    loading, 
    error: queryError ? queryError.message : null, 
    refetch 
  }
}
