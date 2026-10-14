/* Developed by FireSeed - Fueling Innovation */
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'

export interface Recurrencia {
  id: string;
  dia_semana: number;
  hora_inicio: string;
  clase_nombre: string;
  is_active: boolean;
}

export interface ClientProfile {
  name: string
  nombre?: string
  apellido?: string
  email?: string
  telefono?: string
  rol: string
  activePlan: string
  remainingClasses: number
  totalClasses: number
  expirationDate: string
  daysUntilExpiration: number
  recurrencias: Recurrencia[]
  fecha_nacimiento?: string | null
  sexo?: string | null
  contacto_emergencia?: string | null
  notas_medicas?: string | null
  edad?: number | null
  perfil_incompleto?: boolean
  campos_pendientes?: string[]
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
