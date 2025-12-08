import { useMemo } from 'react'
import { useDataContext } from '../../contexts/DataContext'
import type { Node } from '../../types/api'

interface NodeCardProps {
  node: Node
}

export default function NodeCard({ node }: NodeCardProps) {
  const { selectedNode, setSelectedNode } = useDataContext()
  const isSelected = selectedNode?.id === node.id

  const status = useMemo(() => {
    if (!node.last_heard) return 'unknown'
    const lastHeard = new Date(node.last_heard)
    const hourAgo = new Date(Date.now() - 60 * 60 * 1000)
    return lastHeard > hourAgo ? 'online' : 'offline'
  }, [node.last_heard])

  const lastHeardText = useMemo(() => {
    if (!node.last_heard) return 'Never'
    const lastHeard = new Date(node.last_heard)
    const now = new Date()
    const diffMs = now.getTime() - lastHeard.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMins / 60)
    const diffDays = Math.floor(diffHours / 24)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    return `${diffDays}d ago`
  }, [node.last_heard])

  const displayName = node.long_name || node.short_name || node.node_id || `Node ${node.node_num}`

  return (
    <div
      className={`node-card ${isSelected ? 'selected' : ''}`}
      onClick={() => setSelectedNode(isSelected ? null : node)}
    >
      <div className="node-card-header">
        <span className={`node-status ${status}`} />
        <span className="node-name">{displayName}</span>
        {node.short_name && (
          <span className="node-short-name">{node.short_name}</span>
        )}
      </div>
      <div className="node-details">
        {node.latitude && node.longitude ? (
          <span>
            {node.latitude.toFixed(4)}, {node.longitude.toFixed(4)}
          </span>
        ) : (
          <span style={{ color: 'var(--color-text-muted)' }}>No position</span>
        )}
        <span style={{ marginLeft: 'auto' }}>{lastHeardText}</span>
      </div>
    </div>
  )
}
