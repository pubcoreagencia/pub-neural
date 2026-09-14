import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Position, ReactFlowProvider } from "@xyflow/react";
import { RelationEdge, RelationEdgeLabel } from "./RelationEdge";

describe("RelationEdge & RelationEdgeLabel Component", () => {
  it("renders RelationEdgeLabel with relation badge text and style", () => {
    render(
      <RelationEdgeLabel
        labelX={50}
        labelY={50}
        relationType="IMPLEMENTS"
        isActive={true}
        isHighlighted={false}
      />
    );
    expect(screen.getByText("IMPLEMENTS")).toBeDefined();
  });

  it("renders RelationEdgeLabel with active and highlighted states", () => {
    const { unmount } = render(
      <RelationEdgeLabel
        labelX={50}
        labelY={50}
        relationType="USES"
        isActive={true}
        isHighlighted={true}
      />
    );
    expect(screen.getByText("USES")).toBeDefined();
    unmount();

    render(
      <RelationEdgeLabel
        labelX={50}
        labelY={50}
        relationType="SUPERSEDES"
        isActive={false}
        isDimmed={true}
      />
    );
    expect(screen.getByText("SUPERSEDES")).toBeDefined();
  });

  it("renders RelationEdge base path in SVG", () => {
    const { container } = render(
      <ReactFlowProvider>
        <svg>
          <RelationEdge
            id="edge-1"
            source="node-1"
            target="node-2"
            sourceX={0}
            sourceY={0}
            targetX={100}
            targetY={100}
            sourcePosition={Position.Bottom}
            targetPosition={Position.Top}
            data={{
              id: "edge-1",
              source_id: "node-1",
              target_id: "node-2",
              relation_type: "DEPENDS_ON",
              weight: 1.0,
              is_bidirectional: false,
              trust_zone: "tz_internal_holding",
              is_active: true,
            } as any}
          />
        </svg>
      </ReactFlowProvider>
    );
    expect(container.querySelector(".react-flow__edge-path")).toBeDefined();
  });
});
