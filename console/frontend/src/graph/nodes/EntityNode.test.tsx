import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ReactFlowProvider } from "@xyflow/react";
import { EntityNode } from "./EntityNode";
import type { EntityNodeData } from "./EntityNode";

function renderNode(data: Partial<EntityNodeData>) {
  const fullData: EntityNodeData = {
    id: "node-test-1",
    entity_type: "DECISION",
    title: "Test Decision Title",
    slug: "test-decision",
    summary: "Decision summary text",
    promotion_state: "CANDIDATE",
    conflict_state: "NONE",
    confidence_score: 0.95,
    valid_from: "2026-01-01",
    valid_until: null,
    trust_zone: "tz_internal_holding",
    project_id: "pub-ecom",
    evidence_count: 2,
    ...data,
  };

  return render(
    <ReactFlowProvider>
      <EntityNode
        id="node-test-1"
        data={fullData as unknown as Record<string, unknown>}
        selected={false}
        type="entityNode"
        zIndex={1}
        isConnectable={true}
        positionAbsoluteX={0}
        positionAbsoluteY={0}
        dragging={false}
        selectable={true}
        deletable={false}
        draggable={false}
      />
    </ReactFlowProvider>
  );
}

describe("EntityNode Component", () => {
  it("renders DECISION node with title, type, and promotion state", () => {
    renderNode({ entity_type: "DECISION", title: "Architecture Decision" });
    expect(screen.getByText("DECISION")).toBeDefined();
    expect(screen.getByText("Architecture Decision")).toBeDefined();
    expect(screen.getByText("CANDIDATE")).toBeDefined();
    expect(screen.getByText("Conf: 95%")).toBeDefined();
    expect(screen.getByText("Ev: 2")).toBeDefined();
  });

  it("renders RULE node with promotion state", () => {
    renderNode({ entity_type: "RULE", title: "Zero Mutation Rule", promotion_state: "INSTITUTIONAL" });
    expect(screen.getByText("RULE")).toBeDefined();
    expect(screen.getByText("Zero Mutation Rule")).toBeDefined();
    expect(screen.getByText("INSTITUTIONAL")).toBeDefined();
  });

  it("renders PATTERN, LESSON, and fallback unknown entity types", () => {
    const { unmount } = renderNode({ entity_type: "PATTERN", title: "Event Sourcing Pattern" });
    expect(screen.getByText("PATTERN")).toBeDefined();
    unmount();

    renderNode({ entity_type: "CUSTOM_UNKNOWN_TYPE", title: "Unknown Entity" });
    expect(screen.getByText("CUSTOM_UNKNOWN_TYPE")).toBeDefined();
    expect(screen.getByText("Unknown Entity")).toBeDefined();
  });

  it("renders conflict state badge when present", () => {
    renderNode({ conflict_state: "CONTRADICTORY" });
    expect(screen.getByText("CONTRADICTORY")).toBeDefined();
  });
});
