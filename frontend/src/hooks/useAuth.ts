import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchAuthStatus, logout } from '../services/api'

export function useAuth() {
  return useQuery({
    queryKey: ['auth'],
    queryFn: fetchAuthStatus,
    staleTime: 60000, // 1 minute
  })
}

export function useLogout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auth'] })
    },
  })
}
