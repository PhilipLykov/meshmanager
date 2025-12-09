export default function GraphsPage() {
  return (
    <div className="graphs-page">
      <div className="settings-header">
        <h1>Graphs</h1>
      </div>

      <div className="empty-state" style={{ height: '60vh' }}>
        <div className="empty-state-icon">📊</div>
        <h2>Coming Soon</h2>
        <p>Network graphs and visualizations will be available here.</p>
        <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginTop: '1rem' }}>
          Planned features: node connections, signal strength over time, message activity
        </p>
      </div>
    </div>
  )
}
