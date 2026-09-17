import type { Node, Edge } from "@xyflow/react";
import type { GraphNodeDTO, GraphEdgeDTO } from "../api/types";
import type { EntityNodeData } from "./nodes/EntityNode";
import type { RelationEdgeData } from "./edges/RelationEdge";

export function mergeGraphData(
  existingNodes: Node[],
  existingEdges: Edge[],
  newNodes: GraphNodeDTO[],
  newEdges: GraphEdgeDTO[],
  centerNodeId: string | null
): { nodes: Node[]; edges: Edge[] } {
  const nodeMap = new Map<string, Node>();
  const edgeMap = new Map<string, Edge>();

  // Add existing
  existingNodes.forEach((n) => nodeMap.set(n.id, n));
  existingEdges.forEach((e) => edgeMap.set(e.id, e));

  // Merge new nodes
  newNodes.forEach((dto) => {
    const existing = nodeMap.get(dto.id);
    const nodeData: EntityNodeData = {
      ...dto,
      isCenter: dto.id === centerNodeId,
      isSelected: dto.id === centerNodeId,
      isHighlighted: false,
      isDimmed: false,
    };

    nodeMap.set(dto.id, {
      id: dto.id,
      type: "entityNode",
      position: existing ? existing.position : { x: 0, y: 0 },
      data: nodeData as unknown as Record<string, unknown>,
    });
  });

  // Merge new edges
  newEdges.forEach((dto) => {
    const edgeData: RelationEdgeData = {
      ...dto,
      isHighlighted: false,
      isDimmed: false,
    };

    edgeMap.set(dto.id, {
      id: dto.id,
      source: dto.source_id,
      target: dto.target_id,
      type: "relationEdge",
      animated: dto.is_active,
      data: edgeData as unknown as Record<string, unknown>,
    });
  });

  return {
    nodes: Array.from(nodeMap.values()),
    edges: Array.from(edgeMap.values()),
  };
}

export function applyHighlightState(
  nodes: Node[],
  edges: Edge[],
  selectedId: string | null
): { nodes: Node[]; edges: Edge[] } {
  if (!selectedId) {
    return {
      nodes: nodes.map((n) => ({
        ...n,
        data: {
          ...(n.data as unknown as EntityNodeData),
          isSelected: false,
          isHighlighted: false,
          isDimmed: false,
        },
      })),
      edges: edges.map((e) => ({
        ...e,
        data: {
          ...(e.data as unknown as RelationEdgeData),
          isHighlighted: false,
          isDimmed: false,
        },
      })),
    };
  }

  const connectedNodeIds = new Set<string>([selectedId]);
  const connectedEdgeIds = new Set<string>();

  edges.forEach((e) => {
    if (e.source === selectedId || e.target === selectedId) {
      connectedEdgeIds.add(e.id);
      connectedNodeIds.add(e.source);
      connectedNodeIds.add(e.target);
    }
  });

  const updatedNodes = nodes.map((n) => {
    const isSelected = n.id === selectedId;
    const isConnected = connectedNodeIds.has(n.id);
    const data = n.data as unknown as EntityNodeData;

    return {
      ...n,
      data: {
        ...data,
        isSelected,
        isHighlighted: isConnected && !isSelected,
        isDimmed: !isConnected,
      },
    };
  });

  const updatedEdges = edges.map((e) => {
    const isConnected = connectedEdgeIds.has(e.id);
    const data = e.data as unknown as RelationEdgeData;

    return {
      ...e,
      data: {
        ...data,
        isHighlighted: isConnected,
        isDimmed: !isConnected,
      },
    };
  });

  return { nodes: updatedNodes, edges: updatedEdges };
}
