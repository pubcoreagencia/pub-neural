import { useEffect, useState } from "react";
import { NeuralAPI } from "../api/client";
import type { EventDetailDTO } from "../api/types";

interface EventInspectorProps {
  eventId: string | null;
  onSelectEvent?: (eventId: string) => void;
  onNavigateEntity?: (entityId: string) => void;
  onClose?: () => void;
}

export function EventInspector({
  eventId,
  onSelectEvent,
  onNavigateEntity,
  onClose,
}: EventInspectorProps) {
  const [event, setEvent] = useState<EventDetailDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState(false);

  useEffect(() => {
    if (!eventId) {
      setEvent(null);
      setError(null);
      return;
    }

    let active = true;
    setLoading(true);
    setError(null);

    NeuralAPI.getEventDetail(eventId)
      .then((data) => {
        if (active) setEvent(data);
      })
      .catch((err: any) => {
        if (active) {
          setError(err.message || "Failed to load event detail");
          setEvent(null);
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [eventId]);

  const copyId = () => {
    if (!event) return;
    navigator.clipboard.writeText(event.id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  // Detect related entity ID from payload or stream_id
  const getRelatedEntityId = (ev: EventDetailDTO): string | null => {
    if (ev.payload?.node_id && typeof ev.payload.node_id === "string") {
      return ev.payload.node_id;
    }
    if (ev.payload?.entity_id && typeof ev.payload.entity_id === "string") {
      return ev.payload.entity_id;
    }
    if (ev.stream_id.startsWith("entity:")) {
      return ev.stream_id.replace(/^entity:/, "");
    }
    return null;
  };

  if (loading) {
    return (
      <div style={panelContainerStyle}>
        <div style={{ color: "#38bdf8", padding: 24, textAlign: "center", fontSize: "0.85rem" }}>
          Loading Event Inspector...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={panelContainerStyle}>
        <div style={{ color: "#f87171", padding: 24, textAlign: "center", fontSize: "0.85rem" }}>
          {error}
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div style={panelContainerStyle}>
        <div style={{ color: "#64748b", padding: 32, textAlign: "center", fontSize: "0.85rem" }}>
          Select an event in the timeline to inspect audit payload, actor governance, and causal lineage.
        </div>
      </div>
    );
  }

  const relatedEntityId = getRelatedEntityId(event);

  return (
    <div style={panelContainerStyle}>
      {/* 1. IDENTITY HEADER */}
      <div style={{ padding: "16px", borderBottom: "1px solid #334155", backgroundColor: "#0f172a" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 8 }}>
          <span
            style={{
              fontSize: "0.68rem",
              fontWeight: 700,
              textTransform: "uppercase",
              padding: "2px 8px",
              borderRadius: 4,
              backgroundColor: "#1e293b",
              color: "#a855f7",
              border: "1px solid #9333ea",
            }}
          >
            {event.event_type}
          </span>
          <div style={{ display: "flex", gap: 6 }}>
            <button
              type="button"
              onClick={copyId}
              style={{
                background: "transparent",
                border: "1px solid #475569",
                color: copiedId ? "#34d399" : "#94a3b8",
                borderRadius: 4,
                fontSize: "0.65rem",
                cursor: "pointer",
                padding: "2px 6px",
              }}
            >
              {copiedId ? "Copied!" : "Copy ID"}
            </button>
            {onClose && (
              <button
                type="button"
                onClick={onClose}
                title="Close Event View"
                style={{
                  background: "transparent",
                  border: "1px solid #475569",
                  color: "#94a3b8",
                  borderRadius: 4,
                  fontSize: "0.65rem",
                  cursor: "pointer",
                  padding: "2px 6px",
                }}
              >
                ✕
              </button>
            )}
          </div>
        </div>

        <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc", margin: "10px 0 4px 0", lineHeight: 1.3 }}>
          Seq #{event.global_sequence} &bull; {event.event_type}
        </h2>
        <div style={{ fontSize: "0.7rem", color: "#94a3b8", wordBreak: "break-all", fontFamily: "monospace" }}>
          {event.id}
        </div>
      </div>

      <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: 20 }}>
        {/* RELATED ENTITY FOCUS BUTTON */}
        {relatedEntityId && (
          <div
            style={{
              padding: "10px 12px",
              borderRadius: 6,
              backgroundColor: "#0369a1",
              color: "#ffffff",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 8,
            }}
          >
            <div style={{ fontSize: "0.75rem", overflow: "hidden" }}>
              <span style={{ fontWeight: 600 }}>Associated Entity:</span>{" "}
              <span style={{ fontFamily: "monospace", opacity: 0.9 }}>{relatedEntityId.slice(0, 18)}...</span>
            </div>
            <button
              type="button"
              onClick={() => onNavigateEntity && onNavigateEntity(relatedEntityId)}
              style={{
                backgroundColor: "#f8fafc",
                color: "#0369a1",
                border: "none",
                borderRadius: 4,
                padding: "4px 8px",
                fontSize: "0.72rem",
                fontWeight: 700,
                cursor: "pointer",
                whiteSpace: "nowrap",
              }}
            >
              Focus in Graph →
            </button>
          </div>
        )}

        {/* 2. TEMPORAL BOUND: EVENT TIME */}
        <section>
          <div style={sectionTitleStyle}>EVENT TEMPORAL RECORD</div>
          <div style={timeCardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
              <span style={{ fontWeight: 600, color: "#a855f7", fontSize: "0.72rem" }}>
                EVENT TIME (IMMUTABLE LEDGER RECORD)
              </span>
              <span style={{ fontSize: "0.68rem", color: "#94a3b8" }}>Canonical Event Clock</span>
            </div>
            <div style={{ fontSize: "0.78rem", color: "#e2e8f0", fontFamily: "monospace" }}>
              {event.recorded_at}
            </div>
          </div>
        </section>

        {/* 3. ACTOR & STREAM GOVERNANCE */}
        <section>
          <div style={sectionTitleStyle}>ACTOR & STREAM GOVERNANCE</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <div style={metricBoxStyle}>
              <span style={metricLabelStyle}>Actor ID</span>
              <span style={{ color: "#38bdf8", fontSize: "0.72rem", wordBreak: "break-all", fontFamily: "monospace" }}>
                {event.actor_id}
              </span>
            </div>
            <div style={metricBoxStyle}>
              <span style={metricLabelStyle}>Actor Role</span>
              <span style={{ color: "#34d399", fontWeight: 700, fontSize: "0.78rem" }}>
                {event.actor_role}
              </span>
            </div>
            <div style={metricBoxStyle}>
              <span style={metricLabelStyle}>Stream ID</span>
              <span style={{ color: "#cbd5e1", fontSize: "0.72rem", wordBreak: "break-all", fontFamily: "monospace" }}>
                {event.stream_id}
              </span>
            </div>
            <div style={metricBoxStyle}>
              <span style={metricLabelStyle}>Stream Version</span>
              <span style={{ color: "#f8fafc", fontWeight: 700, fontSize: "0.85rem" }}>
                v{event.stream_version}
              </span>
            </div>
          </div>
        </section>

        {/* 4. CAUSAL PARENTS (DAG LINKAGE) */}
        <section>
          <div style={sectionTitleStyle}>
            CAUSAL PREDECESSORS / PARENTS ({event.parent_event_ids.length})
          </div>
          {event.parent_event_ids.length === 0 ? (
            <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
              Root event (no parent causal predecessors recorded).
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {event.parent_event_ids.map((pid) => (
                <div key={pid} style={causalRowStyle}>
                  <span style={{ color: "#94a3b8", fontSize: "0.72rem" }}>Parent ID:</span>
                  <button
                    type="button"
                    onClick={() => onSelectEvent && onSelectEvent(pid)}
                    style={linkButtonStyle}
                    title="Inspect parent event"
                  >
                    {pid}
                  </button>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 5. METADATA & CRYPTO SIGNATURE */}
        <section>
          <div style={sectionTitleStyle}>EVENT METADATA & INTEGRITY</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.75rem" }}>
            <div style={metaRowStyle}>
              <span style={{ color: "#94a3b8" }}>Event Version:</span>
              <span style={{ color: "#f8fafc", fontFamily: "monospace" }}>v{event.event_version}</span>
            </div>
            <div style={metaRowStyle}>
              <span style={{ color: "#94a3b8" }}>Payload Schema Version:</span>
              <span style={{ color: "#f8fafc", fontFamily: "monospace" }}>v{event.payload_schema_version}</span>
            </div>
            <div style={metaRowStyle}>
              <span style={{ color: "#94a3b8" }}>Producer Version:</span>
              <span style={{ color: "#cbd5e1", fontFamily: "monospace" }}>{event.producer_version}</span>
            </div>
            <div style={metaRowStyle}>
              <span style={{ color: "#94a3b8" }}>Cryptographic Signature:</span>
              <span
                style={{
                  color: event.signature ? "#34d399" : "#64748b",
                  fontFamily: "monospace",
                  fontSize: "0.7rem",
                }}
              >
                {event.signature ? `${event.signature.slice(0, 16)}...` : "None (Local Engine Verified)"}
              </span>
            </div>
          </div>
        </section>

        {/* 6. SANITIZED AUDIT PAYLOAD */}
        <section>
          <div style={sectionTitleStyle}>SANITIZED AUDIT PAYLOAD</div>
          <pre
            style={{
              margin: 0,
              padding: "10px",
              backgroundColor: "#0f172a",
              border: "1px solid #334155",
              borderRadius: 6,
              fontSize: "0.72rem",
              fontFamily: "monospace",
              color: "#38bdf8",
              overflowX: "auto",
              maxHeight: "260px",
              lineHeight: 1.4,
            }}
          >
            {JSON.stringify(event.payload, null, 2)}
          </pre>
        </section>
      </div>
    </div>
  );
}

// Styles
const panelContainerStyle: React.CSSProperties = {
  height: "100%",
  boxSizing: "border-box",
  overflowY: "auto",
  backgroundColor: "#131b2e",
  borderLeft: "1px solid #334155",
  fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
};

const sectionTitleStyle: React.CSSProperties = {
  fontSize: "0.68rem",
  fontWeight: 700,
  letterSpacing: "0.06em",
  color: "#94a3b8",
  marginBottom: 8,
  textTransform: "uppercase",
};

const metricBoxStyle: React.CSSProperties = {
  backgroundColor: "#18202f",
  padding: "8px 10px",
  borderRadius: 6,
  border: "1px solid #334155",
  display: "flex",
  flexDirection: "column",
  gap: 2,
};

const metricLabelStyle: React.CSSProperties = {
  fontSize: "0.65rem",
  color: "#64748b",
  textTransform: "uppercase",
  fontWeight: 600,
};

const timeCardStyle: React.CSSProperties = {
  backgroundColor: "#18202f",
  padding: "8px 10px",
  borderRadius: 6,
  border: "1px solid #334155",
};

const causalRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "4px 0",
};

const metaRowStyle: React.CSSProperties = {
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  padding: "3px 0",
  borderBottom: "1px solid #1e293b",
};

const linkButtonStyle: React.CSSProperties = {
  background: "transparent",
  border: "none",
  color: "#38bdf8",
  cursor: "pointer",
  fontFamily: "monospace",
  fontSize: "0.72rem",
  textDecoration: "underline",
  padding: 0,
};
