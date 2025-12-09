import { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import type { TelemetryHistory } from '../../types/api'

// Catppuccin Mocha colors for the chart lines
const SOURCE_COLORS = [
  '#89b4fa', // Blue
  '#a6e3a1', // Green
  '#f9e2af', // Yellow
  '#fab387', // Peach
  '#cba6f7', // Mauve
  '#f38ba8', // Red
  '#94e2d5', // Teal
  '#f5c2e7', // Pink
]

interface TelemetryChartProps {
  data: TelemetryHistory
}

export default function TelemetryChart({ data }: TelemetryChartProps) {
  // Transform data for recharts - group by timestamp and source
  const { chartData, sources } = useMemo(() => {
    // Get unique sources
    const sourceSet = new Set<string>()
    data.data.forEach((point) => {
      sourceSet.add(point.source_name || point.source_id)
    })
    const sources = Array.from(sourceSet)

    // Group data by timestamp (rounded to nearest minute)
    const timeMap = new Map<number, Record<string, number | null>>()

    data.data.forEach((point) => {
      const timestamp = new Date(point.timestamp).getTime()
      // Round to nearest minute for grouping
      const roundedTime = Math.round(timestamp / 60000) * 60000

      if (!timeMap.has(roundedTime)) {
        timeMap.set(roundedTime, { timestamp: roundedTime })
      }

      const entry = timeMap.get(roundedTime)!
      const sourceKey = point.source_name || point.source_id
      entry[sourceKey] = point.value
    })

    // Convert to array and sort by timestamp
    const chartData = Array.from(timeMap.values()).sort(
      (a, b) => (a.timestamp as number) - (b.timestamp as number)
    )

    return { chartData, sources }
  }, [data])

  if (chartData.length === 0) {
    return <div className="telemetry-chart-empty">No data available</div>
  }

  // Format timestamp for X axis
  const formatTime = (timestamp: number) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  // Format tooltip value
  const formatValue = (value: number | null) => {
    if (value === null) return 'N/A'
    return value.toFixed(2)
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTime}
          stroke="var(--color-text-muted)"
          fontSize={10}
          interval="preserveStartEnd"
        />
        <YAxis
          stroke="var(--color-text-muted)"
          fontSize={10}
          width={40}
          tickFormatter={(v) => v.toFixed(1)}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'var(--color-bg-secondary)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text)',
          }}
          labelFormatter={(timestamp) =>
            new Date(timestamp as number).toLocaleString()
          }
          formatter={(value) => [formatValue(value as number | null), '']}
        />
        {sources.length > 1 && (
          <Legend
            wrapperStyle={{ fontSize: '10px' }}
            iconSize={8}
          />
        )}
        {sources.map((source, index) => (
          <Line
            key={source}
            type="monotone"
            dataKey={source}
            name={source}
            stroke={SOURCE_COLORS[index % SOURCE_COLORS.length]}
            strokeWidth={2}
            dot={false}
            connectNulls
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
