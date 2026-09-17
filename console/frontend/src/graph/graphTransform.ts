import type { Node, Edge } from "@xyflow/react";
import type { GraphNodeDTO, GraphEdgeDTO, GraphResponseDTO } from "../api/types";
import type { EntityNodeData } from "./nodes/EntityNode";
import type { RelationEdgeData } from "./edges/RelationEdge";

export function transformNodes(
  dtoNodes: GraphNodeDTO[],
  centerNodeId: string | null
): Node[] {
  return dtoNodes.map((node) => {
    const data: EntityNodeData = {
      ...node,
      label: node.title,
      isCenter: node.id === centerNodeId,
      isSelected: node.id === centerNodeId,
      isHighlighted: false,
      isDimmed: false,
    };

    return {
      id: node.id,
      type: "entityNode",
      data: data as unknown as Record<string, unknown>,
      position: { x: 0, y: 0 },
    };
  });
}

export function transformEdges(dtoEdges: GraphEdgeDTO[]): Edge[] {
  return dtoEdges.map((edge) => {
    const data: RelationEdgeData = {
      ...edge,
      isHighlighted: false,
      isDimmed: false,
    };

    return {
      id: edge.id,
      source: edge.source_id,
      target: edge.target_id,
      type: "relationEdge",
      animated: edge.is_active,
      data: data as unknown as Record<string, unknown>,
    };
  });
}

export function buildGraph(dto: GraphResponseDTO) {
  return {
    nodes: transformNodes(dto.nodes, dto.center_node_id),
    edges: transformEdges(dto.edges),
  };
}
