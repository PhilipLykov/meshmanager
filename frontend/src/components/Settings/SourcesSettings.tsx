import { useState } from 'react'
import { useAdminSources, useDeleteSource, useTestSource } from '../../hooks/useAdminSources'
import { AddSourceForm } from '../Admin/AddSourceForm'

export default function SourcesSettings() {
  const { data: sources = [], isLoading } = useAdminSources()
  const deleteMutation = useDeleteSource()
  const testMutation = useTestSource()
  const [showAddForm, setShowAddForm] = useState(false)
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({})

  const handleDelete = async (id: string, name: string) => {
    if (confirm(`Are you sure you want to delete "${name}"? This will also delete all associated nodes and data.`)) {
      await deleteMutation.mutateAsync(id)
    }
  }

  const handleTest = async (id: string) => {
    try {
      const result = await testMutation.mutateAsync(id)
      setTestResults((prev) => ({ ...prev, [id]: result }))
    } catch (error) {
      setTestResults((prev) => ({
        ...prev,
        [id]: { success: false, message: error instanceof Error ? error.message : 'Test failed' },
      }))
    }
  }

  return (
    <div className="settings-section">
      <div className="settings-section-header">
        <h2>Data Sources</h2>
        <button
          className="btn btn-primary"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          {showAddForm ? 'Cancel' : 'Add Source'}
        </button>
      </div>

      {showAddForm && (
        <div className="settings-card">
          <AddSourceForm onSuccess={() => setShowAddForm(false)} />
        </div>
      )}

      {isLoading ? (
        <div className="loading">
          <div className="loading-spinner" />
          Loading sources...
        </div>
      ) : sources.length === 0 ? (
        <div className="settings-empty">
          No sources configured. Add a MeshMonitor or MQTT source to get started.
        </div>
      ) : (
        <div className="settings-list">
          {sources.map((source) => (
            <div key={source.id} className="settings-card source-card">
              <div className="source-card-header">
                <div className="source-card-title">
                  <span className={`source-status ${source.healthy ? 'healthy' : 'unhealthy'}`} />
                  <span className="source-name">{source.name}</span>
                  <span className="badge">{source.type}</span>
                </div>
                <div className="source-card-status">
                  <span className={`badge ${source.enabled ? 'badge-success' : 'badge-warning'}`}>
                    {source.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>

              {source.url && (
                <div className="source-card-detail">
                  <span className="detail-label">URL:</span>
                  <span className="detail-value">{source.url}</span>
                </div>
              )}

              {source.mqtt_host && (
                <div className="source-card-detail">
                  <span className="detail-label">MQTT Host:</span>
                  <span className="detail-value">{source.mqtt_host}:{source.mqtt_port}</span>
                </div>
              )}

              {testResults[source.id] && (
                <div className={`source-test-result ${testResults[source.id].success ? 'success' : 'error'}`}>
                  {testResults[source.id].message}
                  {testResults[source.id].success && (testResults[source.id] as any).nodes_found !== undefined && (
                    <span> ({(testResults[source.id] as any).nodes_found} nodes found)</span>
                  )}
                </div>
              )}

              <div className="source-card-actions">
                <button
                  className="btn btn-secondary btn-sm"
                  onClick={() => handleTest(source.id)}
                  disabled={testMutation.isPending}
                >
                  {testMutation.isPending ? 'Testing...' : 'Test Connection'}
                </button>
                <button
                  className="btn btn-danger btn-sm"
                  onClick={() => handleDelete(source.id, source.name)}
                  disabled={deleteMutation.isPending}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
