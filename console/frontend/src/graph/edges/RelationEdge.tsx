import { memo } from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getSmoothStepPath,
  type EdgeProps,
} from "@xyflow/react";
import type { GraphEdgeDTO } from "../../api/types";

export interface RelationEdgeData extends GraphEdgeDTO {
  isHighlighted?: boolean;
  isDimmed?: boolean;
}

export function RelationEdgeLabel({
  labelX,
  labelY,
  relationType,
  isActive,
  isHighlighted,
  isDimmed,
}: {
  labelX: number;
  labelY: number;
  relationType: string;
  isActive: boolean;
  isHighlighted?: boolean;
  isDimmed?: boolean;
}) {
  return (
    <div
      data-testid="relation-edge-label"
      style={{
        position: "absolute",
        transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
        pointerEvents: "all",
        fontSize: "0.62rem",
        fontWeight: 700,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        padding: "2px 6px",
        borderRadius: 10,
        backgroundColor: isHighlighted ? "#0284c7" : "#1e293b",
        color: isHighlighted ? "#ffffff" : "#94a3b8",
        border: `1px solid ${isHighlighted ? "#38bdf8" : "#334155"}`,
        boxShadow: isHighlighted ? "0 0 8px rgba(56, 189, 248, 0.5)" : "0 1px 4px rgba(0, 0, 0, 0.4)",
        opacity: isDimmed ? 0.2 : 1.0,
        cursor: "pointer",
        transition: "all 0.2s ease",
        userSelect: "none",
      }}
      title={`Relation: ${relationType} (${isActive ? "Active" : "Inactive"})`}
    >
      {relationType}
    </div>
  );
}

export const RelationEdge = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
}: EdgeProps) => {
  const edgeData = data as unknown as RelationEdgeData;

  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 16,
  });

  const isHighlighted = edgeData?.isHighlighted;
  const isDimmed = edgeData?.isDimmed;
  const isActive = edgeData?.is_active ?? true;
  const isProposed = edgeData?.association_status === "PROPOSED";
  const isConfirmed = edgeData?.association_status === "CONFIRMED";

  const strokeColor = isHighlighted
    ? "#38bdf8"
    : isProposed
    ? "#f59e0b"
    : isConfirmed
    ? "#10b981"
    : isActive
    ? "#64748b"
    : "#334155";

  const strokeWidth = isHighlighted ? 2.5 : isProposed || isConfirmed ? 2.0 : 1.5;
  const strokeDash = isProposed ? "5,5" : isActive ? undefined : "5,5";

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke: strokeColor,
          strokeWidth,
          opacity: isDimmed ? 0.2 : 1.0,
          strokeDasharray: strokeDash,
          transition: "stroke 0.2s ease, opacity 0.2s ease",
        }}
      />
      <EdgeLabelRenderer>
        <RelationEdgeLabel
          labelX={labelX}
          labelY={labelY}
          relationType={edgeData?.relation_type || "RELATED_TO"}
          isActive={isActive}
          isHighlighted={isHighlighted}
          isDimmed={isDimmed}
        />
      </EdgeLabelRenderer>
    </>
  );
});

RelationEdge.displayName = "RelationEdge";
