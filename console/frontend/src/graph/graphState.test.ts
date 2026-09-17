import { describe, it, expect } from "vitest";
import { mergeGraphData, applyHighlightState } from "./graphState";
import type { GraphNodeDTO, GraphEdgeDTO } from "../api/types";
import type { Node, Edge } from "@xyflow/react";
import type { EntityNodeData } from "./nodes/EntityNode";

describe("graphState management", () => {
  const nodeA: GraphNodeDTO = {
    id: "node-A",
    entity_type: "DECISION",
    title: "Decision A",
    slug: "decision-a",
    summary: null,
    promotion_state: "CANDIDATE",
    conflict_state: "NONE",
    confidence_score: 1.0,
    valid_from: "2026-01-01",
    valid_until: null,
    trust_zone: "tz_internal_holding",
    project_id: "pub-ecom",
    evidence_count: 1,
  };

  const nodeB: GraphNodeDTO = {
    id: "node-B",
    entity_type: "RULE",
    title: "Rule B",
    slug: "rule-b",
    summary: null,
    promotion_state: "INSTITUTIONAL",
    conflict_state: "NONE",
    confidence_score: 1.0,
    valid_from: "2026-01-01",
    valid_until: null,
    trust_zone: "tz_internal_holding",
    project_id: "pub-ecom",
    evidence_count: 0,
  };

  const edgeAB: GraphEdgeDTO = {
    id: "edge-AB",
    source_id: "node-A",
    target_id: "node-B",
    relation_type: "IMPLEMENTS",
    weight: 1.0,
    is_bidirectional: false,
    trust_zone: "tz_internal_holding",
    is_active: true,
  };

  it("merges new nodes and edges without duplicates", () => {
    const existingNodes: Node[] = [];
    const existingEdges: Edge[] = [];

    // Pass 1: add node A and B
    const step1 = mergeGraphData(existingNodes, existingEdges, [nodeA, nodeB], [edgeAB], "node-A");
    expect(step1.nodes.length).toBe(2);
    expect(step1.edges.length).toBe(1);

    // Pass 2: duplicate add of node A and B
    const step2 = mergeGraphData(step1.nodes, step1.edges, [nodeA, nodeB], [edgeAB], "node-A");
    expect(step2.nodes.length).toBe(2);
    expect(step2.edges.length).toBe(1);

    // Pass 3: add node C
    const nodeC: GraphNodeDTO = { ...nodeB, id: "node-C", title: "Rule C" };
    const edgeBC: GraphEdgeDTO = { ...edgeAB, id: "edge-BC", source_id: "node-B", target_id: "node-C" };

    const step3 = mergeGraphData(step2.nodes, step2.edges, [nodeC], [edgeBC], "node-A");
    expect(step3.nodes.length).toBe(3);
    expect(step3.edges.length).toBe(2);
  });

  it("applies connected neighborhood highlighting and dims unrelated nodes", () => {
    const nodes: Node[] = [
      { id: "node-A", type: "entityNode", position: { x: 0, y: 0 }, data: { id: "node-A" } },
      { id: "node-B", type: "entityNode", position: { x: 0, y: 0 }, data: { id: "node-B" } },
      { id: "node-C", type: "entityNode", position: { x: 0, y: 0 }, data: { id: "node-C" } },
    ];

    const edges: Edge[] = [
      { id: "edge-AB", source: "node-A", target: "node-B", type: "relationEdge", data: { id: "edge-AB" } },
    ];

    // Select node-A: node-B is connected, node-C is unconnected
    const highlighted = applyHighlightState(nodes, edges, "node-A");

    const dataA = highlighted.nodes.find((n) => n.id === "node-A")?.data as unknown as EntityNodeData;
    const dataB = highlighted.nodes.find((n) => n.id === "node-B")?.data as unknown as EntityNodeData;
    const dataC = highlighted.nodes.find((n) => n.id === "node-C")?.data as unknown as EntityNodeData;

    expect(dataA.isSelected).toBe(true);
    expect(dataA.isDimmed).toBe(false);

    expect(dataB.isHighlighted).toBe(true);
    expect(dataB.isDimmed).toBe(false);

    expect(dataC.isDimmed).toBe(true);
    expect(dataC.isHighlighted).toBe(false);
  });
});
