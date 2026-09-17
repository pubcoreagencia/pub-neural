import { useEffect, useState } from "react";
import { NeuralAPI } from "../api/client";
import type { EdgeDetailDTO } from "../api/types";

interface EdgeInspectorProps {
  edgeId: string | null;
  onNavigateEntity?: (id: string) => void;
  onClose?: () => void;
}

export function EdgeInspector({ edgeId, onNavigateEntity, onClose }: EdgeInspectorProps) {
  const [edge, setEdge] = useState<EdgeDetailDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!edgeId) {
      setEdge(null);
      return;
    }

    let active = true;
    setLoading(true);
    setError(null);

    NeuralAPI.getEdgeDetail(edgeId)
      .then((data) => {
        if (active) setEdge(data);
      })
      .catch((err) => {
        console.error("Failed to load edge detail", err);
        if (active) setError(err.message || "Failed to load edge details.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [edgeId]);

  if (!edgeId) {
    return (
      <div style={{ padding: 16, color: "#64748b", textAlign: "center", fontSize: "0.85rem" }}>
        Select an edge in the graph to inspect relationship details, provenance, and grounded evidence.
      </div>
    );
  }

  if (loading) {
    return (
      <div style={{ padding: 16, color: "#38bdf8", textAlign: "center", fontSize: "0.85rem" }}>
        Loading edge details...
      </div>
    );
  }

  if (error || !edge) {
    return (
      <div style={{ padding: 16, color: "#ef4444", fontSize: "0.85rem" }}>
        {error || "Edge not found or unauthorized."}
      </div>
    );
  }

  const isContradiction = edge.relation_type === "CONTRADICTS";

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflowY: "auto", padding: 16, color: "#f8fafc" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <span
          style={{
            fontSize: "0.7rem",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            padding: "2px 8px",
            borderRadius: 4,
            backgroundColor: isContradiction ? "#7f1d1d" : "#1e293b",
            color: isContradiction ? "#fecaca" : "#38bdf8",
            border: `1px solid ${isContradiction ? "#ef4444" : "#0284c7"}`,
          }}
        >
          {edge.relation_type}
        </span>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            style={{
              background: "transparent",
              border: "none",
              color: "#94a3b8",
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            ✕
          </button>
        )}
      </div>

      {/* Triplet Connected Endpoints */}
      <div style={{ backgroundColor: "#1e293b", padding: 12, borderRadius: 8, marginBottom: 14, border: "1px solid #334155" }}>
        <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: 4 }}>Source Entity:</div>
        <div
          onClick={() => onNavigateEntity?.(edge.source_id)}
          style={{
            fontSize: "0.85rem",
            color: "#38bdf8",
            fontWeight: 600,
            cursor: onNavigateEntity ? "pointer" : "default",
            wordBreak: "break-all",
            marginBottom: 8,
          }}
        >
          {edge.source_id}
        </div>

        <div style={{ fontSize: "0.75rem", color: "#94a3b8", marginBottom: 4 }}>Target Entity:</div>
        <div
          onClick={() => onNavigateEntity?.(edge.target_id)}
          style={{
            fontSize: "0.85rem",
            color: "#38bdf8",
            fontWeight: 600,
            cursor: onNavigateEntity ? "pointer" : "default",
            wordBreak: "break-all",
          }}
        >
          {edge.target_id}
        </div>
      </div>

      {/* Provenance & Epistemic Attributes */}
      <div style={{ marginBottom: 14, fontSize: "0.8rem", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
        <div style={{ backgroundColor: "#1e293b", padding: 8, borderRadius: 6 }}>
          <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Epistemic State</div>
          <div style={{ fontWeight: 600, color: edge.epistemic_classification === "EXTRACTED" ? "#34d399" : "#fbbf24" }}>
            {edge.epistemic_classification}
          </div>
        </div>

        <div style={{ backgroundColor: "#1e293b", padding: 8, borderRadius: 6 }}>
          <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Confidence</div>
          <div style={{ fontWeight: 600, color: "#f8fafc" }}>
            {(edge.confidence * 100).toFixed(0)}%
          </div>
        </div>

        <div style={{ backgroundColor: "#1e293b", padding: 8, borderRadius: 6 }}>
          <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Extractor</div>
          <div style={{ fontWeight: 500, color: "#cbd5e1" }}>{edge.extractor}</div>
        </div>

        <div style={{ backgroundColor: "#1e293b", padding: 8, borderRadius: 6 }}>
          <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>Trust Zone</div>
          <div style={{ fontWeight: 500, color: "#cbd5e1" }}>{edge.trust_zone}</div>
        </div>
      </div>

      {/* Grounded Evidence Locators */}
      <div style={{ marginTop: 8 }}>
        <div style={{ fontSize: "0.75rem", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", marginBottom: 8 }}>
          Grounded Evidence ({edge.evidence.length})
        </div>
        {edge.evidence.length === 0 ? (
          <div style={{ fontSize: "0.8rem", color: "#64748b", fontStyle: "italic" }}>
            No direct code slice attached to this edge.
          </div>
        ) : (
          edge.evidence.map((ev) => (
            <div
              key={ev.id}
              style={{
                backgroundColor: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 6,
                padding: 10,
                marginBottom: 8,
                fontSize: "0.8rem",
              }}
            >
              <div style={{ color: "#38bdf8", fontWeight: 600, marginBottom: 4 }}>
                {ev.file_path || "Source Blob"} (L{ev.start_line}–L{ev.end_line})
              </div>
              <pre
                style={{
                  margin: 0,
                  padding: "6px 8px",
                  backgroundColor: "#1e293b",
                  borderRadius: 4,
                  fontSize: "0.75rem",
                  color: "#e2e8f0",
                  whiteSpace: "pre-wrap",
                  fontFamily: "monospace",
                }}
              >
                {ev.exact_quote}
              </pre>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
