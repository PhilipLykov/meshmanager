import { useQuery } from '@tanstack/react-query'
import { fetchNodes } from '../services/api'

export function useNodes(options?: { sourceId?: string; activeOnly?: boolean; activeHours?: number }) {
  return useQuery({
    queryKey: ['nodes', options],
    queryFn: () => fetchNodes(options),
  })
}
