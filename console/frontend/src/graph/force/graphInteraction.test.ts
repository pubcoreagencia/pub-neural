import { describe, it, expect } from "vitest";
import { calculateDegreesAndHighlights } from "./graphInteraction";
import type { ForceNodeObject, ForceLinkObject } from "./graphTypes";

describe("graphInteraction", () => {
  it("computes degrees and neighbor highlights for active node", () => {
    const nodes: ForceNodeObject[] = [
      {
        id: "node-1",
        entity_type: "DECISION",
        title: "Dec 1",
        slug: "dec-1",
        summary: null,
        promotion_state: "VALIDATED",
        conflict_state: "RESOLVED",
        confidence_score: 1.0,
        valid_from: "2026-09-17T00:00:00Z",
        valid_until: null,
        trust_zone: "tz_internal_holding",
        project_id: "pub-ecom",
        evidence_count: 2,
      },
      {
        id: "node-2",
        entity_type: "RULE",
        title: "Rule 1",
        slug: "rule-1",
        summary: null,
        promotion_state: "VALIDATED",
        conflict_state: "RESOLVED",
        confidence_score: 1.0,
        valid_from: "2026-09-17T00:00:00Z",
        valid_until: null,
        trust_zone: "tz_internal_holding",
        project_id: null,
        evidence_count: 1,
      },
      {
        id: "node-3",
        entity_type: "CONCEPT",
        title: "Concept 1",
        slug: "concept-1",
        summary: null,
        promotion_state: "CANDIDATE",
        conflict_state: "RESOLVED",
        confidence_score: 0.8,
        valid_from: "2026-09-17T00:00:00Z",
        valid_until: null,
        trust_zone: "tz_internal_holding",
        project_id: null,
        evidence_count: 0,
      },
    ];

    const links: ForceLinkObject[] = [
      {
        id: "edge-1",
        source: "node-1",
        target: "node-2",
        relation_type: "IMPLEMENTS",
        weight: 1.0,
        is_bidirectional: false,
        trust_zone: "tz_internal_holding",
        is_active: true,
      },
    ];

    // Select node-1
    const { nodes: updatedNodes, links: updatedLinks } = calculateDegreesAndHighlights(
      nodes,
      links,
      "node-1"
    );

    const n1 = updatedNodes.find((n) => n.id === "node-1");
    const n2 = updatedNodes.find((n) => n.id === "node-2");
    const n3 = updatedNodes.find((n) => n.id === "node-3");

    expect(n1?.degree).toBe(1);
    expect(n1?.isSelected).toBe(true);
    expect(n1?.isDimmed).toBe(false);

    expect(n2?.degree).toBe(1);
    expect(n2?.isNeighbor).toBe(true);
    expect(n2?.isDimmed).toBe(false);

    // Node 3 is not connected to node-1, so it should be dimmed
    expect(n3?.degree).toBe(1); // default min
    expect(n3?.isDimmed).toBe(true);

    expect(updatedLinks[0].isSelected).toBe(true);
    expect(updatedLinks[0].isDimmed).toBe(false);
  });
});
