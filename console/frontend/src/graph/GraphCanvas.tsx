import { useEffect, useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
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
import { EntityNode, type EntityNodeData } from "./nodes/EntityNode";
import { RelationEdge } from "./edges/RelationEdge";
import { GraphLegend } from "./GraphLegend";
import { mergeGraphData, applyHighlightState } from "./graphState";

interface GraphCanvasProps {
  entityId: string | null;
  onNodeSelect?: (nodeId: string) => void;
}

function GraphCanvasInternal({ entityId, onNodeSelect }: GraphCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { fitView } = useReactFlow();

  const nodeTypes = useMemo(() => ({ entityNode: EntityNode }), []);
  const edgeTypes = useMemo(() => ({ relationEdge: RelationEdge }), []);

  const loadGraph = useCallback(
    async (id: string) => {
      setLoading(true);
      setError(null);
      try {
        const data = await NeuralAPI.getNeighborhood(id, 2);
        const { nodes: rawNodes, edges: rawEdges } = buildGraph(data);
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
          rawNodes,
          rawEdges
        );
        const { nodes: highlightedNodes, edges: highlightedEdges } = applyHighlightState(
          layoutedNodes,
          layoutedEdges,
          id
        );
        setNodes(highlightedNodes);
        setEdges(highlightedEdges);

        setTimeout(() => {
          fitView({ duration: 500, padding: 0.2 });
        }, 50);
      } catch (e: any) {
        console.error("Failed to load graph", e);
        setError(e.message || "Failed to load neighborhood graph.");
      } finally {
        setLoading(false);
      }
    },
    [setNodes, setEdges, fitView]
  );

  const expandNeighborhood = useCallback(async () => {
    if (!entityId) return;
    setLoading(true);
    try {
      const data = await NeuralAPI.getNeighborhood(entityId, 1);
      const merged = mergeGraphData(nodes, edges, data.nodes, data.edges, entityId);
      const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
        merged.nodes,
        merged.edges
      );
      const { nodes: highlightedNodes, edges: highlightedEdges } = applyHighlightState(
        layoutedNodes,
        layoutedEdges,
        entityId
      );
      setNodes(highlightedNodes);
      setEdges(highlightedEdges);

      setTimeout(() => {
        fitView({ duration: 500, padding: 0.2 });
      }, 50);
    } catch (e: any) {
      console.error("Failed to expand neighborhood", e);
      setError(e.message || "Failed to expand neighborhood.");
    } finally {
      setLoading(false);
    }
  }, [entityId, nodes, edges, setNodes, setEdges, fitView]);

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
      if (onNodeSelect) {
        onNodeSelect(node.id);
      }
      const { nodes: hNodes, edges: hEdges } = applyHighlightState(nodes, edges, node.id);
      setNodes(hNodes);
      setEdges(hEdges);
    },
    [onNodeSelect, nodes, edges, setNodes, setEdges]
  );

  const onPaneClickInternal = useCallback(() => {
    const { nodes: hNodes, edges: hEdges } = applyHighlightState(nodes, edges, null);
    setNodes(hNodes);
    setEdges(hEdges);
  }, [nodes, edges, setNodes, setEdges]);

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", backgroundColor: "#0f172a" }}>
      {/* Action Bar */}
      <div
        style={{
          position: "absolute",
          top: 16,
          right: 16,
          zIndex: 10,
          display: "flex",
          gap: 8,
          alignItems: "center",
        }}
      >
        {entityId && (
          <button
            type="button"
            onClick={expandNeighborhood}
            disabled={loading}
            style={{
              padding: "6px 12px",
              backgroundColor: "#1e293b",
              color: "#38bdf8",
              border: "1px solid #0284c7",
              borderRadius: 6,
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <span>+ Expand Neighborhood</span>
          </button>
        )}

        <button
          type="button"
          onClick={() => fitView({ duration: 400, padding: 0.2 })}
          style={{
            padding: "6px 12px",
            backgroundColor: "#1e293b",
            color: "#e2e8f0",
            border: "1px solid #334155",
            borderRadius: 6,
            fontSize: "0.75rem",
            fontWeight: 600,
            cursor: "pointer",
            boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
          }}
        >
          Reset View
        </button>
      </div>

      {loading && (
        <div
          style={{
            position: "absolute",
            top: 20,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 10,
            backgroundColor: "rgba(15, 23, 42, 0.9)",
            color: "#38bdf8",
            padding: "4px 12px",
            borderRadius: 20,
            fontSize: "0.75rem",
            fontWeight: 600,
            border: "1px solid #0284c7",
            boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
          }}
        >
          Traversing Knowledge Graph...
        </div>
      )}

      {error && (
        <div
          style={{
            position: "absolute",
            top: 20,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 10,
            backgroundColor: "rgba(127, 29, 29, 0.9)",
            color: "#fecaca",
            padding: "6px 14px",
            borderRadius: 6,
            fontSize: "0.8rem",
            border: "1px solid #ef4444",
          }}
        >
          {error}
        </div>
      )}

      {nodes.length === 0 && !loading && (
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            color: "#64748b",
            textAlign: "center",
            fontSize: "0.9rem",
          }}
        >
          <div style={{ fontSize: "1.8rem", marginBottom: 8 }}>✦</div>
          Search or select an entity from the explorer to explore its relationship graph.
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClickInternal}
        onPaneClick={onPaneClickInternal}
        minZoom={0.2}
        maxZoom={2.5}
        fitView
      >
        <Background color="#334155" gap={20} size={1} />
        <Controls
          style={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: 6,
            fill: "#f1f5f9",
          }}
        />
        <MiniMap
          nodeColor={(n) => {
            const data = n.data as unknown as EntityNodeData;
            return data?.isCenter ? "#38bdf8" : "#64748b";
          }}
          style={{
            backgroundColor: "rgba(15, 23, 42, 0.8)",
            border: "1px solid #334155",
            borderRadius: 6,
          }}
        />
      </ReactFlow>

      <GraphLegend />
    </div>
  );
}

export function GraphCanvas(props: GraphCanvasProps) {
  return (
    <ReactFlowProvider>
      <GraphCanvasInternal {...props} />
    </ReactFlowProvider>
  );
}
