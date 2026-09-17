import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import ForceGraph from "force-graph";
import { NeuralAPI } from "../../api/client";
import { renderCanvasNode, renderCanvasLink } from "./graphRender";
import { calculateDegreesAndHighlights } from "./graphInteraction";
import type { ForceNodeObject, ForceLinkObject, GraphFilterCriteria } from "./graphTypes";
import type { GraphResponseDTO } from "../../api/types";

interface GraphCanvasForceProps {
  selectedEntityId: string | null;
  onNodeSelect?: (nodeId: string) => void;
  onEdgeSelect?: (edgeId: string) => void;
  onClearSelection?: () => void;
}

export function GraphCanvasForce({
  selectedEntityId,
  onNodeSelect,
  onEdgeSelect,
  onClearSelection,
}: GraphCanvasForceProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphInstanceRef = useRef<any>(null);

  const [rawNodes, setRawNodes] = useState<ForceNodeObject[]>([]);
  const [rawLinks, setRawLinks] = useState<ForceLinkObject[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState<string>("Initializing Graph...");
  const [error, setError] = useState<string | null>(null);

  // Hover state
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null);

  // View Source Mode: "unified" (Physical + Cognitive), "git" (Physical 55 Repos), or "backbone" (Institutional Cognitive)
  const [sourceMode, setSourceMode] = useState<"unified" | "git" | "backbone">("unified");

  // Filters state
  const [filters, setFilters] = useState<GraphFilterCriteria>({
    searchQuery: "",
    entityTypes: [],
    relationTypes: [],
    projectScope: "",
    trustZone: "",
    epistemicState: "ALL",
  });

  // 1a. Load Unified Physical + Cognitive Graph (Holding 55 Repos + Cognitive Backbone + Evidence Bridges)
  const loadUnifiedGraph = useCallback(async () => {
    setLoading(true);
    setLoadingStatus("Connecting Physical Codebase (55 Repos) + Institutional Memory...");
    setError(null);
    try {
      const data: GraphResponseDTO = await NeuralAPI.getUnifiedGraph({
        source: "all",
        limit: 120,
      });
      const nodes: ForceNodeObject[] = data.nodes.map((n) => ({ ...n }));
      const links: ForceLinkObject[] = data.edges.map((e) => ({
        ...e,
        source: e.source_id,
        target: e.target_id,
      }));
      setRawNodes(nodes);
      setRawLinks(links);
    } catch (e: any) {
      console.error("Failed to load unified graph", e);
      setError(e.message || "Failed to load unified graph.");
    } finally {
      setLoading(false);
    }
  }, []);

  // 1b. Load Canonical Git Topology: PUB Core Holding (All 55 Repositories)
  const loadGitTopology = useCallback(async () => {
    setLoading(true);
    setLoadingStatus("Traversing PUB Core Holding (55 repositories)...");
    setError(null);
    try {
      // Empty repository param loads organization root + all 55 repositories
      const data: GraphResponseDTO = await NeuralAPI.getRepositoryGraph({
        limit: 100,
      });
      const nodes: ForceNodeObject[] = data.nodes.map((n) => ({ ...n }));
      const links: ForceLinkObject[] = data.edges.map((e) => ({
        ...e,
        source: e.source_id,
        target: e.target_id,
      }));
      setRawNodes(nodes);
      setRawLinks(links);
    } catch (e: any) {
      console.error("Failed to load Git organization topology", e);
      setError(e.message || "Failed to load Git organization topology.");
    } finally {
      setLoading(false);
    }
  }, []);

  // 1c. Load Institutional Backbone
  const loadBackbone = useCallback(async () => {
    setLoading(true);
    setLoadingStatus("Traversing Institutional Backbone...");
    setError(null);
    try {
      const data: GraphResponseDTO = await NeuralAPI.getGraphBackbone({ limit: 120 });
      const nodes: ForceNodeObject[] = data.nodes.map((n) => ({ ...n }));
      const links: ForceLinkObject[] = data.edges.map((e) => ({
        ...e,
        source: e.source_id,
        target: e.target_id,
      }));
      setRawNodes(nodes);
      setRawLinks(links);
    } catch (e: any) {
      console.error("Failed to load graph backbone", e);
      setError(e.message || "Failed to load graph backbone.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (sourceMode === "unified") {
      loadUnifiedGraph();
    } else if (sourceMode === "git") {
      loadGitTopology();
    } else {
      loadBackbone();
    }
  }, [sourceMode, loadUnifiedGraph, loadGitTopology, loadBackbone]);

  // 2. Incremental Expansion on click, double click or manual trigger
  const expandNode = useCallback(
    async (nodeId: string) => {
      setLoading(true);
      setLoadingStatus(`Expanding node ${nodeId}...`);
      try {
        let data: GraphResponseDTO;
        if (nodeId.startsWith("dir:")) {
          // Format: dir:repo@branch:path
          const parts = nodeId.split(":");
          const repoBranch = parts[1];
          const subPath = parts.slice(2).join(":");
          const [repoName, branchName] = repoBranch.split("@");
          data = await NeuralAPI.getRepositoryGraph({
            repository: repoName,
            branch: branchName || "main",
            path: subPath,
            depth: 1,
            limit: 50,
          });
        } else if (nodeId.startsWith("repo:")) {
          const repoFull = nodeId.replace("repo:", "");
          data = await NeuralAPI.getRepositoryGraph({
            repository: repoFull,
            path: "",
            depth: 1,
            limit: 50,
          });
        } else if (nodeId.startsWith("org:")) {
          data = await NeuralAPI.getRepositoryGraph({
            limit: 100,
          });
        } else {
          data = await NeuralAPI.getNeighborhood(nodeId, 1, { limit: 50 });
        }

        setRawNodes((prevNodes) => {
          const existingIds = new Set(prevNodes.map((n) => n.id));
          const newNodes = data.nodes
            .filter((n) => !existingIds.has(n.id))
            .map((n) => ({ ...n }));
          return [...prevNodes, ...newNodes];
        });
        setRawLinks((prevLinks) => {
          const existingEdgeIds = new Set(prevLinks.map((l) => l.id));
          const newLinks = data.edges
            .filter((e) => !existingEdgeIds.has(e.id))
            .map((e) => ({
              ...e,
              source: e.source_id,
              target: e.target_id,
            }));
          return [...prevLinks, ...newLinks];
        });
      } catch (e: any) {
        console.error("Failed to expand node neighborhood", e);
        setError(e.message || "Failed to expand neighborhood.");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // 3. Filter nodes and links based on UI toolbar
  const filteredData = useMemo(() => {
    let nodes = rawNodes;
    let links = rawLinks;

    if (filters.searchQuery.trim()) {
      const q = filters.searchQuery.toLowerCase();
      nodes = nodes.filter(
        (n) =>
          n.id.toLowerCase().includes(q) ||
          n.title.toLowerCase().includes(q) ||
          (n.summary && n.summary.toLowerCase().includes(q))
      );
    }

    if (filters.entityTypes.length > 0) {
      nodes = nodes.filter((n) => filters.entityTypes.includes(n.entity_type));
    }

    if (filters.epistemicState === "CONFIRMED") {
      nodes = nodes.filter((n) =>
        ["CONFIRMED", "VALIDATED", "ADOPTED", "INSTITUTIONAL"].includes(n.promotion_state)
      );
    } else if (filters.epistemicState === "PROPOSED") {
      nodes = nodes.filter((n) =>
        ["PROPOSED", "CANDIDATE", "CAPTURED", "EXTRACTED"].includes(n.promotion_state)
      );
    }

    if (filters.projectScope) {
      nodes = nodes.filter((n) => n.project_id === filters.projectScope);
    }

    const visibleNodeIds = new Set(nodes.map((n) => n.id));
    links = links.filter((l) => {
      const sId = typeof l.source === "object" ? (l.source as any).id : l.source;
      const tId = typeof l.target === "object" ? (l.target as any).id : l.target;
      return visibleNodeIds.has(sId) && visibleNodeIds.has(tId);
    });

    // Apply active highlight/degree calculation
    const activeId = hoveredNodeId || selectedEntityId;
    return calculateDegreesAndHighlights(nodes, links, activeId);
  }, [rawNodes, rawLinks, filters, hoveredNodeId, selectedEntityId]);

  // 4. Initialize force-graph instance in DOM container
  useEffect(() => {
    if (!containerRef.current) return;

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    const graph = new (ForceGraph as any)(containerRef.current)
      .width(width)
      .height(height)
      .backgroundColor("#0f172a")
      .nodeId("id")
      .nodeLabel((node: ForceNodeObject) => `${node.entity_type}: ${node.title}`)
      .nodeCanvasObject((node: ForceNodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
        renderCanvasNode(node, ctx, globalScale);
      })
      .nodeCanvasObjectMode(() => "replace")
      .linkCanvasObject((link: ForceLinkObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
        renderCanvasLink(link, ctx, globalScale);
      })
      .linkCanvasObjectMode(() => "replace")
      .onNodeClick((node: ForceNodeObject) => {
        if (onNodeSelect) {
          onNodeSelect(node.id);
        }
      })
      .onLinkClick((link: ForceLinkObject) => {
        if (onEdgeSelect) {
          onEdgeSelect(link.id);
        }
      })
      .onBackgroundClick(() => {
        if (onClearSelection) {
          onClearSelection();
        }
      })
      .onNodeHover((node: ForceNodeObject | null) => {
        setHoveredNodeId(node ? node.id : null);
      })
      .onNodeRightClick((node: ForceNodeObject) => {
        // Right click expands node
        expandNode(node.id);
      })
      .d3AlphaDecay(0.02)
      .d3VelocityDecay(0.3)
      .warmupTicks(30);

    // Tune physics force properties
    graph.d3Force("charge")?.strength(-180);
    graph.d3Force("link")?.distance(60);

    graphInstanceRef.current = graph;

    const handleResize = () => {
      if (containerRef.current && graphInstanceRef.current) {
        graphInstanceRef.current
          .width(containerRef.current.clientWidth)
          .height(containerRef.current.clientHeight);
      }
    };

    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      if (graphInstanceRef.current) {
        graphInstanceRef.current._destructor?.();
      }
    };
  }, [onNodeSelect, onEdgeSelect, onClearSelection, expandNode]);

  // 5. Update graph data when filteredData changes
  useEffect(() => {
    if (graphInstanceRef.current) {
      graphInstanceRef.current.graphData({
        nodes: filteredData.nodes,
        links: filteredData.links,
      });
    }
  }, [filteredData]);

  // Fit View handler
  const handleResetView = () => {
    if (graphInstanceRef.current) {
      graphInstanceRef.current.zoomToFit(400, 40);
    }
  };

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", backgroundColor: "#0f172a", overflow: "hidden" }}>
      {/* Top Controls & Search Bar */}
      <div
        style={{
          position: "absolute",
          top: 14,
          left: 16,
          right: 16,
          zIndex: 20,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          pointerEvents: "none",
        }}
      >
        {/* Search & Epistemic Filter */}
        <div style={{ display: "flex", gap: 8, alignItems: "center", pointerEvents: "auto" }}>
          <input
            type="text"
            placeholder="Search nodes in graph..."
            value={filters.searchQuery}
            onChange={(e) => setFilters((f) => ({ ...f, searchQuery: e.target.value }))}
            style={{
              padding: "6px 12px",
              backgroundColor: "rgba(30, 41, 59, 0.85)",
              color: "#f8fafc",
              border: "1px solid #334155",
              borderRadius: 6,
              fontSize: "0.8rem",
              width: 220,
              outline: "none",
              backdropFilter: "blur(4px)",
            }}
          />

          <select
            value={filters.epistemicState}
            onChange={(e) => setFilters((f) => ({ ...f, epistemicState: e.target.value as any }))}
            style={{
              padding: "6px 10px",
              backgroundColor: "rgba(30, 41, 59, 0.85)",
              color: "#e2e8f0",
              border: "1px solid #334155",
              borderRadius: 6,
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            <option value="ALL">All States</option>
            <option value="CONFIRMED">Confirmed / Validated</option>
            <option value="PROPOSED">Proposed / Candidate</option>
          </select>
        </div>

        {/* Action Buttons */}
        <div style={{ display: "flex", gap: 8, pointerEvents: "auto" }}>
          {/* Source of Truth Mode Selector */}
          <div
            style={{
              display: "flex",
              backgroundColor: "rgba(30, 41, 59, 0.85)",
              border: "1px solid #334155",
              borderRadius: 6,
              padding: 2,
              gap: 2,
            }}
          >
            <button
              type="button"
              onClick={() => setSourceMode("unified")}
              style={{
                padding: "4px 10px",
                backgroundColor: sourceMode === "unified" ? "#0284c7" : "transparent",
                color: sourceMode === "unified" ? "#ffffff" : "#94a3b8",
                border: "none",
                borderRadius: 4,
                fontSize: "0.72rem",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              Unified 🧠🌲
            </button>
            <button
              type="button"
              onClick={() => setSourceMode("git")}
              style={{
                padding: "4px 10px",
                backgroundColor: sourceMode === "git" ? "#0369a1" : "transparent",
                color: sourceMode === "git" ? "#ffffff" : "#94a3b8",
                border: "none",
                borderRadius: 4,
                fontSize: "0.72rem",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              Git Source 🌲
            </button>
            <button
              type="button"
              onClick={() => setSourceMode("backbone")}
              style={{
                padding: "4px 10px",
                backgroundColor: sourceMode === "backbone" ? "#4f46e5" : "transparent",
                color: sourceMode === "backbone" ? "#ffffff" : "#94a3b8",
                border: "none",
                borderRadius: 4,
                fontSize: "0.72rem",
                fontWeight: 600,
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              Institutional 🏛️
            </button>
          </div>

          {selectedEntityId && (
            <button
              type="button"
              onClick={() => expandNode(selectedEntityId)}
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
              }}
            >
              + Expand Selected
            </button>
          )}

          <button
            type="button"
            onClick={sourceMode === "unified" ? loadUnifiedGraph : sourceMode === "git" ? loadGitTopology : loadBackbone}
            disabled={loading}
            style={{
              padding: "6px 12px",
              backgroundColor: "#1e293b",
              color: "#a78bfa",
              border: "1px solid #6366f1",
              borderRadius: 6,
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            Refresh
          </button>

          <button
            type="button"
            onClick={handleResetView}
            style={{
              padding: "6px 12px",
              backgroundColor: "#1e293b",
              color: "#e2e8f0",
              border: "1px solid #334155",
              borderRadius: 6,
              fontSize: "0.75rem",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Reset View
          </button>
        </div>
      </div>

      {/* Loading Indicator */}
      {loading && (
        <div
          style={{
            position: "absolute",
            top: 60,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 30,
            backgroundColor: "rgba(15, 23, 42, 0.9)",
            color: "#38bdf8",
            padding: "5px 14px",
            borderRadius: 20,
            fontSize: "0.75rem",
            fontWeight: 600,
            border: "1px solid #0284c7",
            boxShadow: "0 4px 12px rgba(0,0,0,0.5)",
          }}
        >
          {loadingStatus}
        </div>
      )}

      {/* Error Indicator */}
      {error && (
        <div
          style={{
            position: "absolute",
            top: 60,
            left: "50%",
            transform: "translateX(-50%)",
            zIndex: 30,
            backgroundColor: "rgba(127, 29, 29, 0.9)",
            color: "#fecaca",
            padding: "6px 14px",
            borderRadius: 6,
            fontSize: "0.75rem",
            border: "1px solid #ef4444",
          }}
        >
          {error}
        </div>
      )}

      {/* Empty State */}
      {filteredData.nodes.length === 0 && !loading && (
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            color: "#64748b",
            textAlign: "center",
            fontSize: "0.85rem",
            zIndex: 10,
          }}
        >
          <div style={{ fontSize: "1.8rem", marginBottom: 8 }}>✦</div>
          No nodes match current filters. Adjust search or reload backbone.
        </div>
      )}

      {/* Canvas DOM Container */}
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
    </div>
  );
}
