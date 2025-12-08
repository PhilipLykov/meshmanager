import axios from 'axios'
import type { AuthStatus, MeshMonitorSourceCreate, MqttSourceCreate, Node, Source } from '../types/api'

const api = axios.create({
  baseURL: '',
  withCredentials: true,
})

// Sources
export async function fetchSources(): Promise<Source[]> {
  const response = await api.get<Source[]>('/api/sources')
  return response.data
}

export async function fetchAdminSources(): Promise<Source[]> {
  const response = await api.get<Source[]>('/api/admin/sources')
  return response.data
}

export async function createMeshMonitorSource(data: MeshMonitorSourceCreate): Promise<Source> {
  const response = await api.post<Source>('/api/admin/sources/meshmonitor', data)
  return response.data
}

export async function createMqttSource(data: MqttSourceCreate): Promise<Source> {
  const response = await api.post<Source>('/api/admin/sources/mqtt', data)
  return response.data
}

export async function deleteSource(id: string): Promise<void> {
  await api.delete(`/api/admin/sources/${id}`)
}

export async function testSource(id: string): Promise<{ success: boolean; message: string }> {
  const response = await api.post<{ success: boolean; message: string }>(`/api/admin/sources/${id}/test`)
  return response.data
}

// Nodes
export async function fetchNodes(options?: { sourceId?: string; activeOnly?: boolean }): Promise<Node[]> {
  const params = new URLSearchParams()
  if (options?.sourceId) params.append('source_id', options.sourceId)
  if (options?.activeOnly) params.append('active_only', 'true')

  const response = await api.get<Node[]>(`/api/nodes?${params.toString()}`)
  return response.data
}

export async function fetchNode(id: string): Promise<Node> {
  const response = await api.get<Node>(`/api/nodes/${id}`)
  return response.data
}

// Auth
export async function fetchAuthStatus(): Promise<AuthStatus> {
  const response = await api.get<AuthStatus>('/auth/status')
  return response.data
}

export async function logout(): Promise<void> {
  await api.post('/auth/logout')
}

// Health
export async function fetchHealth(): Promise<{ status: string; database: string; version: string }> {
  const response = await api.get<{ status: string; database: string; version: string }>('/health')
  return response.data
}
