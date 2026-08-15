/* Developed by FireSeed - Fueling Innovation */
import { useState, useEffect, useCallback } from 'react'
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
  activePlan: string
  remainingClasses: number
  totalClasses: number
  expirationDate: string
  daysUntilExpiration: number
  recurrencias: Recurrencia[]
}

export function useClientProfile() {
  const [profile, setProfile] = useState<ClientProfile | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProfile = useCallback(async () => {
    try {
      setLoading(true)
      const response = await api.get('/profile/')
      setProfile(response.data)
      setError(null)
    } catch (err: any) {
      console.error('Error fetching profile:', err)
      setError(err.message)
      setProfile(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchProfile()
  }, [fetchProfile])

  return { profile, loading, error, refetch: fetchProfile }
}
