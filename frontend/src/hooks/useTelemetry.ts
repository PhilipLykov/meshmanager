import { useQuery } from '@tanstack/react-query'
import { fetchTelemetry, fetchTelemetryHistory } from '../services/api'

export function useTelemetry(nodeNum: number | undefined, hours?: number) {
  return useQuery({
    queryKey: ['telemetry', nodeNum, hours],
    queryFn: () => fetchTelemetry(nodeNum!, hours),
    enabled: nodeNum !== undefined,
  })
}

export function useTelemetryHistory(nodeNum: number | undefined, metric: string, hours?: number) {
  return useQuery({
    queryKey: ['telemetry-history', nodeNum, metric, hours],
    queryFn: () => fetchTelemetryHistory(nodeNum!, metric, hours),
    enabled: nodeNum !== undefined,
  })
}
