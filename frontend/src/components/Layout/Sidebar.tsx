import { useMemo } from 'react'
import { useNodes } from '../../hooks/useNodes'
import { useSources } from '../../hooks/useSources'
import { useDataContext } from '../../contexts/DataContext'
import { useAuthContext } from '../../contexts/AuthContext'
import NodeList from '../NodeList/NodeList'

export default function Sidebar() {
  const { filterSourceId, showActiveOnly, setShowActiveOnly } = useDataContext()
  const { isAdmin } = useAuthContext()

  const { data: sources = [], isLoading: sourcesLoading } = useSources()
  const { data: nodes = [], isLoading: nodesLoading } = useNodes({
    sourceId: filterSourceId ?? undefined,
    activeOnly: showActiveOnly,
  })

  // Group nodes by source
  const nodesBySource = useMemo(() => {
    const grouped = new Map<string, typeof nodes>()
    for (const node of nodes) {
      const sourceId = node.source_id
      if (!grouped.has(sourceId)) {
        grouped.set(sourceId, [])
      }
      grouped.get(sourceId)!.push(node)
    }
    return grouped
  }, [nodes])

  const isLoading = sourcesLoading || nodesLoading

  return (
    <aside className="sidebar">
      <div className="node-list-header">
        <h2>Nodes ({nodes.length})</h2>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.75rem', color: 'var(--color-text-secondary)', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={showActiveOnly}
            onChange={(e) => setShowActiveOnly(e.target.checked)}
          />
          Active only
        </label>
      </div>

      {isLoading ? (
        <div className="loading">
          <div className="loading-spinner" />
          Loading...
        </div>
      ) : nodes.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📡</div>
          <p>No nodes found</p>
          {isAdmin && <p style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>Add a source to get started</p>}
        </div>
      ) : (
        <div className="node-list">
          {sources.map((source) => {
            const sourceNodes = nodesBySource.get(source.id) || []
            if (sourceNodes.length === 0 && filterSourceId !== source.id) return null

            return (
              <div key={source.id} className="source-section">
                <div className="source-header">
                  <span className={`source-status ${source.healthy ? 'healthy' : 'unhealthy'}`} />
                  {source.name} ({sourceNodes.length})
                </div>
                <NodeList nodes={sourceNodes} />
              </div>
            )
          })}
        </div>
      )}

      {isAdmin && (
        <div className="admin-panel">
          <h3>Admin</h3>
          <button className="btn btn-secondary" style={{ width: '100%' }} onClick={() => window.location.href = '/admin'}>
            Manage Sources
          </button>
        </div>
      )}
    </aside>
  )
}
