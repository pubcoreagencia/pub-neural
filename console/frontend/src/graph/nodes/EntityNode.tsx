import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { GraphNodeDTO } from "../../api/types";

export interface EntityNodeData extends GraphNodeDTO {
  label?: string;
  isCenter?: boolean;
  isSelected?: boolean;
  isHighlighted?: boolean;
  isDimmed?: boolean;
}

const ENTITY_COLORS: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  DECISION: { bg: "#1f1b2e", border: "#8b5cf6", text: "#e9d5ff", badge: "#4c1d95" },
  RULE: { bg: "#2a1e12", border: "#f59e0b", text: "#fef3c7", badge: "#78350f" },
  PATTERN: { bg: "#112629", border: "#06b6d4", text: "#cffafe", badge: "#164e63" },
  LESSON: { bg: "#13271d", border: "#10b981", text: "#d1fae5", badge: "#064e3b" },
  HOLDING: { bg: "#2d1b4e", border: "#a855f7", text: "#f3e8ff", badge: "#6b21a8" },
  PROJECT: { bg: "#142136", border: "#3b82f6", text: "#dbeafe", badge: "#1e3a8a" },
  REPOSITORY: { bg: "#1b212b", border: "#64748b", text: "#e2e8f0", badge: "#334155" },
  EVIDENCE: { bg: "#122333", border: "#0284c7", text: "#e0f2fe", badge: "#075985" },
  SOURCE: { bg: "#1e2229", border: "#6b7280", text: "#f3f4f6", badge: "#374151" },
  EVENT: { bg: "#2a151b", border: "#e11d48", text: "#ffe4e6", badge: "#881337" },
  DOCUMENT: { bg: "#282313", border: "#eab308", text: "#fef9c3", badge: "#713f12" },
  SKILL: { bg: "#28152e", border: "#d946ef", text: "#fae8ff", badge: "#701a75" },
  AGENT: { bg: "#291522", border: "#ec4899", text: "#fce7f3", badge: "#831843" },
  CONCEPT: { bg: "#221933", border: "#a855f7", text: "#f3e8ff", badge: "#581c87" },
};

const DEFAULT_THEME = { bg: "#1a1f26", border: "#94a3b8", text: "#f1f5f9", badge: "#334155" };

export const EntityNode = memo(({ data }: NodeProps) => {
  const nodeData = data as unknown as EntityNodeData;
  const theme = ENTITY_COLORS[nodeData.entity_type?.toUpperCase()] || DEFAULT_THEME;

  const isSelected = nodeData.isSelected || nodeData.isCenter;
  const isDimmed = nodeData.isDimmed;

  return (
    <div
      tabIndex={0}
      role="button"
      aria-label={`${nodeData.entity_type} entity: ${nodeData.title}`}
      style={{
        width: 240,
        borderRadius: 8,
        backgroundColor: theme.bg,
        border: `2px solid ${isSelected ? "#38bdf8" : nodeData.isHighlighted ? "#a78bfa" : theme.border}`,
        boxShadow: isSelected
          ? "0 0 15px rgba(56, 189, 248, 0.5)"
          : nodeData.isHighlighted
          ? "0 0 10px rgba(167, 139, 250, 0.4)"
          : "0 2px 8px rgba(0, 0, 0, 0.3)",
        opacity: isDimmed ? 0.35 : 1.0,
        transition: "all 0.2s ease-in-out",
        cursor: "pointer",
        outline: "none",
        color: "#f8fafc",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        padding: "10px 12px",
        boxSizing: "border-box",
      }}
    >
      <Handle type="target" position={Position.Top} style={{ background: theme.border, width: 8, height: 8 }} />

      {/* Card Header: Type Tag + Promotion State */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <span
          style={{
            fontSize: "0.68rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            padding: "2px 6px",
            borderRadius: 4,
            backgroundColor: theme.badge,
            color: theme.text,
          }}
        >
          {nodeData.entity_type || "ENTITY"}
        </span>

        <span
          style={{
            fontSize: "0.65rem",
            fontWeight: 600,
            padding: "1px 5px",
            borderRadius: 4,
            backgroundColor: "rgba(255, 255, 255, 0.08)",
            color: nodeData.promotion_state === "INSTITUTIONAL" ? "#34d399" : "#cbd5e1",
          }}
        >
          {nodeData.promotion_state || "DRAFT"}
        </span>
      </div>

      {/* Card Body: Title */}
      <div
        style={{
          fontSize: "0.85rem",
          fontWeight: 600,
          lineHeight: 1.3,
          color: "#ffffff",
          marginBottom: 6,
          overflow: "hidden",
          textOverflow: "ellipsis",
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
        }}
        title={nodeData.title}
      >
        {nodeData.title}
      </div>

      {/* Card Footer: Metadata (Confidence, Conflict, Evidence) */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.68rem",
          color: "#94a3b8",
          borderTop: "1px solid rgba(255, 255, 255, 0.08)",
          paddingTop: 4,
        }}
      >
        <span>
          Conf: {nodeData.confidence_score !== undefined ? `${Math.round(nodeData.confidence_score * 100)}%` : "N/A"}
        </span>

        {nodeData.conflict_state && nodeData.conflict_state !== "NONE" && nodeData.conflict_state !== "RESOLVED" && (
          <span
            style={{
              color: "#f87171",
              fontWeight: 700,
              backgroundColor: "rgba(239, 68, 68, 0.15)",
              padding: "1px 4px",
              borderRadius: 3,
            }}
          >
            {nodeData.conflict_state}
          </span>
        )}

        {nodeData.evidence_count > 0 && (
          <span style={{ color: "#38bdf8" }}>
            Ev: {nodeData.evidence_count}
          </span>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} style={{ background: theme.border, width: 8, height: 8 }} />
    </div>
  );
});

EntityNode.displayName = "EntityNode";
