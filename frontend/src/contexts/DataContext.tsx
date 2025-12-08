import { createContext, useContext, useState, type ReactNode } from 'react'
import type { Node } from '../types/api'

interface DataContextValue {
  selectedNode: Node | null
  setSelectedNode: (node: Node | null) => void
  filterSourceId: string | null
  setFilterSourceId: (sourceId: string | null) => void
  showActiveOnly: boolean
  setShowActiveOnly: (active: boolean) => void
}

const DataContext = createContext<DataContextValue | null>(null)

export function DataProvider({ children }: { children: ReactNode }) {
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [filterSourceId, setFilterSourceId] = useState<string | null>(null)
  const [showActiveOnly, setShowActiveOnly] = useState(false)

  const value: DataContextValue = {
    selectedNode,
    setSelectedNode,
    filterSourceId,
    setFilterSourceId,
    showActiveOnly,
    setShowActiveOnly,
  }

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}

export function useDataContext() {
  const context = useContext(DataContext)
  if (!context) {
    throw new Error('useDataContext must be used within a DataProvider')
  }
  return context
}
