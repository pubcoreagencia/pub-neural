import { describe, it, expect, vi } from "vitest";
import { getNodeRadius, renderCanvasNode } from "./graphRender";
import type { ForceNodeObject } from "./graphTypes";

describe("graphRender - Project and Organization layer visualization", () => {
  it("computes prominent radii for ORGANIZATION and PROJECT entities", () => {
    const orgNode: ForceNodeObject = {
      id: "org:pubcoreagencia",
      entity_type: "ORGANIZATION",
      title: "PUB CORE HOLDING",
      slug: "pubcoreagencia",
      summary: null,
      promotion_state: "INSTITUTIONAL",
      conflict_state: "RESOLVED",
      confidence_score: 1.0,
      valid_from: "2026-09-17T00:00:00Z",
      valid_until: null,
      trust_zone: "tz_internal_holding",
      project_id: null,
      evidence_count: 0,
      degree: 34,
    };

    const projectNode: ForceNodeObject = {
      id: "proj:pub-neural",
      entity_type: "PROJECT",
      title: "🏛️ PUB Neural",
      slug: "pub-neural",
      summary: "Neural Project",
      promotion_state: "INSTITUTIONAL",
      conflict_state: "RESOLVED",
      confidence_score: 1.0,
      valid_from: "2026-09-17T00:00:00Z",
      valid_until: null,
      trust_zone: "tz_internal_holding",
      project_id: "pub-neural",
      evidence_count: 10,
      degree: 4,
    };

    const repoNode: ForceNodeObject = {
      id: "repo:pubcoreagencia/pub-neural",
      entity_type: "REPOSITORY",
      title: "pubcoreagencia/pub-neural",
      slug: "repo-pub-neural",
      summary: null,
      promotion_state: "EXTRACTED",
      conflict_state: "RESOLVED",
      confidence_score: 1.0,
      valid_from: "2026-09-17T00:00:00Z",
      valid_until: null,
      trust_zone: "tz_internal_holding",
      project_id: "pub-neural",
      evidence_count: 2,
      degree: 2,
    };

    const orgRadius = getNodeRadius(orgNode);
    const projRadius = getNodeRadius(projectNode);
    const repoRadius = getNodeRadius(repoNode);

    // Organization is the root apex (24)
    expect(orgRadius).toBe(24);

    // Project layer is prominent (between 15 and 24)
    expect(projRadius).toBeGreaterThanOrEqual(15);
    expect(projRadius).toBeLessThanOrEqual(24);

    // Repositories are smaller leaves
    expect(repoRadius).toBeLessThan(projRadius);
  });

  it("renders PROJECT and ORGANIZATION titles early even at lower zoom levels", () => {
    const projectNode: ForceNodeObject = {
      id: "proj:pub-ecom",
      entity_type: "PROJECT",
      title: "🏛️ PUB E-Commerce",
      slug: "pub-ecom",
      summary: null,
      promotion_state: "INSTITUTIONAL",
      conflict_state: "RESOLVED",
      confidence_score: 1.0,
      valid_from: "2026-09-17T00:00:00Z",
      valid_until: null,
      trust_zone: "tz_internal_holding",
      project_id: "pub-ecom",
      evidence_count: 0,
    };

    const mockCtx = {
      save: vi.fn(),
      restore: vi.fn(),
      beginPath: vi.fn(),
      arc: vi.fn(),
      fill: vi.fn(),
      stroke: vi.fn(),
      fillText: vi.fn(),
      setLineDash: vi.fn(),
    } as unknown as CanvasRenderingContext2D;

    // Call render at globalScale 0.5 (where ordinary nodes would hide titles)
    renderCanvasNode(projectNode, mockCtx, 0.5);

    // Check that fillText was called with the project title
    expect(mockCtx.fillText).toHaveBeenCalledWith(
      "PROJECT",
      expect.any(Number),
      expect.any(Number)
    );
    expect(mockCtx.fillText).toHaveBeenCalledWith(
      "🏛️ PUB E-Commerce",
      expect.any(Number),
      expect.any(Number)
    );
  });
});
