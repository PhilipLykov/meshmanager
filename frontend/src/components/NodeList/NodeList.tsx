import type { Node } from '../../types/api'
import NodeCard from './NodeCard'

interface NodeListProps {
  nodes: Node[]
}

export default function NodeList({ nodes }: NodeListProps) {
  return (
    <div>
      {nodes.map((node) => (
        <NodeCard key={node.id} node={node} />
      ))}
    </div>
  )
}
