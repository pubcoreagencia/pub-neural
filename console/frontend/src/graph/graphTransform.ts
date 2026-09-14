import type { Node, Edge } from "@xyflow/react";
import type { GraphNodeDTO, GraphEdgeDTO, GraphResponseDTO } from "../api/types";

export function transformNodes(
  dtoNodes: GraphNodeDTO[],
  centerNodeId: string | null
): Node[] {
  return dtoNodes.map((node) => ({
    id: node.id,
    type: "default",
    data: {
      label: node.title,
      type: node.entity_type,
      isCenter: node.id === centerNodeId,
      ...node,
    },
    position: { x: 0, y: 0 }, // Position will be calculated by Dagre
  }));
}

export function transformEdges(dtoEdges: GraphEdgeDTO[]): Edge[] {
  return dtoEdges.map((edge) => ({
    id: edge.id,
    source: edge.source_id,
    target: edge.target_id,
    label: edge.relation_type,
    type: "default",
    animated: edge.is_active,
    data: edge as unknown as Record<string, unknown>,
  }));
}

export function buildGraph(dto: GraphResponseDTO) {
  return {
    nodes: transformNodes(dto.nodes, dto.center_node_id),
    edges: transformEdges(dto.edges),
  };
}
