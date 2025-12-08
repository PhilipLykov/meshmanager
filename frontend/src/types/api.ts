export interface Source {
  id: string
  name: string
  type: 'meshmonitor' | 'mqtt'
  enabled: boolean
  healthy: boolean
}

export interface Node {
  id: string
  source_id: string
  source_name: string | null
  node_num: number
  node_id: string | null
  short_name: string | null
  long_name: string | null
  latitude: number | null
  longitude: number | null
  last_heard: string | null
}

export interface NodeDetail extends Node {
  hw_model: string | null
  role: string | null
  altitude: number | null
  position_time: string | null
  position_precision_bits: number | null
  is_licensed: boolean
  first_seen: string
  updated_at: string
}

export interface AuthStatus {
  authenticated: boolean
  user: UserInfo | null
  oidc_enabled: boolean
}

export interface UserInfo {
  id: string
  email: string | null
  display_name: string | null
  is_admin: boolean
}

export interface SourceCreate {
  name: string
  enabled?: boolean
}

export interface MeshMonitorSourceCreate extends SourceCreate {
  url: string
  api_token?: string
  poll_interval_seconds?: number
}

export interface MqttSourceCreate extends SourceCreate {
  mqtt_host: string
  mqtt_port?: number
  mqtt_username?: string
  mqtt_password?: string
  mqtt_topic_pattern: string
  mqtt_use_tls?: boolean
}
