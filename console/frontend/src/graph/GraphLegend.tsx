import { useState } from "react";

export function GraphLegend() {
  const [expanded, setExpanded] = useState(false);
  const categories = [
    { label: "HOLDING", color: "#a855f7" },
    { label: "PROJECT", color: "#3b82f6" },
    { label: "REPOSITORY", color: "#64748b" },
    { label: "DECISION", color: "#8b5cf6" },
    { label: "RULE", color: "#f59e0b" },
    { label: "PATTERN", color: "#06b6d4" },
    { label: "LESSON", color: "#10b981" },
    { label: "EVIDENCE", color: "#0284c7" },
    { label: "EVENT", color: "#e11d48" },
  ];

  const relations = [
    "USES",
    "DEPENDS_ON",
    "IMPLEMENTS",
    "DERIVED_FROM",
    "VALIDATED_BY",
    "SUPERSEDES",
  ];

  return (
    <div
      style={{
        position: "absolute",
        bottom: 16,
        left: 16,
        zIndex: 10,
        backgroundColor: "rgba(15, 23, 42, 0.85)",
        backdropFilter: "blur(8px)",
        border: "1px solid #334155",
        borderRadius: 8,
        color: "#e2e8f0",
        fontSize: "0.75rem",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
        boxShadow: "0 4px 12px rgba(0,0,0,0.4)",
        overflow: "hidden",
        maxWidth: 280,
      }}
    >
      <div
        onClick={() => setExpanded(!expanded)}
        style={{
          padding: "8px 12px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          cursor: "pointer",
          userSelect: "none",
          backgroundColor: "rgba(30, 41, 59, 0.5)",
          fontWeight: 600,
        }}
      >
        <span>Knowledge Graph Legend</span>
        <span style={{ fontSize: "0.7rem", color: "#94a3b8" }}>{expanded ? "▼" : "▲"}</span>
      </div>

      {expanded && (
        <div style={{ padding: "10px 12px", display: "flex", flexDirection: "column", gap: 10 }}>
          <div>
            <div style={{ fontWeight: 600, color: "#94a3b8", marginBottom: 6, fontSize: "0.68rem" }}>
              ENTITY TYPES
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 4 }}>
              {categories.map((c) => (
                <div key={c.label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      backgroundColor: c.color,
                      display: "inline-block",
                    }}
                  />
                  <span>{c.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <div style={{ fontWeight: 600, color: "#94a3b8", marginBottom: 4, fontSize: "0.68rem" }}>
              RELATION TYPES
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {relations.map((r) => (
                <span
                  key={r}
                  style={{
                    backgroundColor: "#1e293b",
                    padding: "1px 5px",
                    borderRadius: 4,
                    fontSize: "0.62rem",
                    border: "1px solid #334155",
                  }}
                >
                  {r}
                </span>
              ))}
            </div>
          </div>

          <div>
            <div style={{ fontWeight: 600, color: "#94a3b8", marginBottom: 4, fontSize: "0.68rem" }}>
              LIFECYCLE
            </div>
            <div style={{ display: "flex", gap: 6, fontSize: "0.65rem" }}>
              <span style={{ color: "#34d399" }}>● INSTITUTIONAL</span>
              <span style={{ color: "#cbd5e1" }}>● CANDIDATE</span>
              <span style={{ color: "#f87171" }}>● CONFLICT</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
