import { useEffect, useCallback } from "react";
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { NeuralAPI } from "../api/client";
import { buildGraph } from "./graphTransform";
import { getLayoutedElements } from "./layout";

interface GraphCanvasProps {
  entityId: string | null;
  onNodeClick?: (nodeId: string) => void;
}

export function GraphCanvas({ entityId, onNodeClick }: GraphCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const loadGraph = useCallback(async (id: string) => {
    try {
      const data = await NeuralAPI.getNeighborhood(id);
      const { nodes: initialNodes, edges: initialEdges } = buildGraph(data);
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        initialNodes,
        initialEdges
      );
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
    } catch (e) {
      console.error("Failed to load graph", e);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    if (entityId) {
      loadGraph(entityId);
    } else {
      setNodes([]);
      setEdges([]);
    }
  }, [entityId, loadGraph, setNodes, setEdges]);

  const onNodeClickInternal = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (onNodeClick) {
        onNodeClick(node.id);
      }
    },
    [onNodeClick]
  );

  return (
    <div style={{ width: "100%", height: "100%" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickInternal}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  );
}
