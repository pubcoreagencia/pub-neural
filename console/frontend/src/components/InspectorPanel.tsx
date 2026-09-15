import { useEffect, useState } from "react";
import { NeuralAPI } from "../api/client";
import type { EntityDetailDTO } from "../api/types";
import { EventInspector } from "../inspector/EventInspector";

interface InspectorPanelProps {
  entityId: string | null;
  eventId?: string | null;
  activeTab?: "entity" | "event";
  onTabChange?: (tab: "entity" | "event") => void;
  onNavigateEntity?: (id: string) => void;
  onSelectEvent?: (eventId: string) => void;
  onCloseEvent?: () => void;
}

export function InspectorPanel({
  entityId,
  eventId,
  activeTab,
  onTabChange,
  onNavigateEntity,
  onSelectEvent,
  onCloseEvent,
}: InspectorPanelProps) {
  const [entity, setEntity] = useState<EntityDetailDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState(false);
  const [internalTab, setInternalTab] = useState<"entity" | "event">("entity");

  const currentTab = activeTab ?? internalTab;

  const setTab = (tab: "entity" | "event") => {
    if (onTabChange) onTabChange(tab);
    setInternalTab(tab);
  };

  useEffect(() => {
    if (eventId && !entityId) {
      setTab("event");
    } else if (entityId && !eventId) {
      setTab("entity");
    }
  }, [entityId, eventId]);

  useEffect(() => {
    if (!entityId) {
      setEntity(null);
      return;
    }

    let active = true;
    setLoading(true);
    NeuralAPI.getEntityDetail(entityId)
      .then((data) => {
        if (active) setEntity(data);
      })
      .catch((err) => {
        console.error("Failed to load entity detail", err);
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [entityId]);

  const copyId = () => {
    if (!entity) return;
    navigator.clipboard.writeText(entity.id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  if (currentTab === "event" && eventId) {
    return (
      <div style={panelContainerStyle}>
        {entityId && (
          <div style={tabBarStyle}>
            <button
              type="button"
              onClick={() => setTab("entity")}
              style={{
                ...tabBtnStyle,
                color: "#94a3b8",
                borderBottom: "2px solid transparent",
              }}
            >
              ✦ Entity Inspector
            </button>
            <button
              type="button"
              onClick={() => setTab("event")}
              style={{
                ...tabBtnStyle,
                color: "#a855f7",
                borderBottom: "2px solid #a855f7",
                backgroundColor: "#1e293b",
              }}
            >
              ◷ Event Inspector
            </button>
          </div>
        )}
        <EventInspector
          eventId={eventId}
          onSelectEvent={onSelectEvent}
          onNavigateEntity={(id) => {
            if (onNavigateEntity) onNavigateEntity(id);
            setTab("entity");
          }}
          onClose={onCloseEvent}
        />
      </div>
    );
  }

  if (loading) {
    return (
      <div style={panelContainerStyle}>
        <div style={{ color: "#38bdf8", padding: 24, textAlign: "center", fontSize: "0.85rem" }}>
          Loading Entity Inspector...
        </div>
      </div>
    );
  }

  if (!entity) {
    if (eventId) {
      return (
        <div style={panelContainerStyle}>
          <EventInspector
            eventId={eventId}
            onSelectEvent={onSelectEvent}
            onNavigateEntity={(id) => {
              if (onNavigateEntity) onNavigateEntity(id);
              setTab("entity");
            }}
            onClose={onCloseEvent}
          />
        </div>
      );
    }
    return (
      <div style={panelContainerStyle}>
        <div style={{ color: "#64748b", padding: 32, textAlign: "center", fontSize: "0.85rem" }}>
          Select an entity node in the canvas or search explorer to inspect deep provenance, temporal bounds, and causal lineage.
        </div>
      </div>
    );
  }

  return (
    <div style={panelContainerStyle}>
      {eventId && (
        <div style={tabBarStyle}>
          <button
            type="button"
            onClick={() => setTab("entity")}
            style={{
              ...tabBtnStyle,
              color: "#38bdf8",
              borderBottom: "2px solid #38bdf8",
              backgroundColor: "#1e293b",
            }}
          >
            ✦ Entity Inspector
          </button>
          <button
            type="button"
            onClick={() => setTab("event")}
            style={{
              ...tabBtnStyle,
              color: "#94a3b8",
              borderBottom: "2px solid transparent",
            }}
          >
            ◷ Event Inspector
          </button>
        </div>
      )}

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
              color: "#38bdf8",
              border: "1px solid #0284c7",
            }}
          >
            {entity.entity_type}
          </span>
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
        </div>

        <h2 style={{ fontSize: "1.1rem", fontWeight: 700, color: "#f8fafc", margin: "10px 0 4px 0", lineHeight: 1.3 }}>
          {entity.title}
        </h2>
        <div style={{ fontSize: "0.7rem", color: "#94a3b8", wordBreak: "break-all", fontFamily: "monospace" }}>
          {entity.id}
        </div>
      </div>

      <div style={{ padding: "16px", display: "flex", flexDirection: "column", gap: 20 }}>
        {/* 2. STATE & LIFECYCLE */}
        <section>
          <div style={sectionTitleStyle}>LIFECYCLE & GOVERNANCE STATE</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            <div style={metricBoxStyle}>
              <span style={metricLabelStyle}>Promotion</span>
              <span style={{ color: "#34d399", fontWeight: 700 }}>{entity.promotion_state}</span>
            </div>
            <div style={metricBoxStyle}>
              <span style={metricLabelStyle}>Conflict</span>
              <span
                style={{
                  color: entity.conflict_state === "NONE" ? "#94a3b8" : "#f87171",
                  fontWeight: entity.conflict_state === "NONE" ? 500 : 700,
                }}
              >
                {entity.conflict_state}
              </span>
            </div>
            <div style={metricBoxStyle}>
              <span style={metricLabelStyle}>Confidence</span>
              <span style={{ color: "#38bdf8", fontWeight: 700 }}>
                {Math.round(entity.confidence_score * 100)}%
              </span>
            </div>
            <div style={metricBoxStyle}>
              <span style={metricLabelStyle}>Trust Zone</span>
              <span style={{ color: "#cbd5e1", fontSize: "0.72rem" }}>{entity.trust_zone}</span>
            </div>
          </div>
        </section>

        {/* 3. NARRATIVE / SUMMARY & CONTENT */}
        {(entity.summary || entity.content) && (
          <section>
            <div style={sectionTitleStyle}>NARRATIVE DEFINITION</div>
            {entity.summary && (
              <div
                style={{
                  padding: "10px 12px",
                  borderRadius: 6,
                  backgroundColor: "#1e293b",
                  borderLeft: "3px solid #38bdf8",
                  fontSize: "0.8rem",
                  color: "#e2e8f0",
                  lineHeight: 1.4,
                  marginBottom: entity.content ? 8 : 0,
                }}
              >
                {entity.summary}
              </div>
            )}
            {entity.content && (
              <div
                style={{
                  padding: "10px",
                  borderRadius: 6,
                  backgroundColor: "#18202f",
                  fontSize: "0.78rem",
                  color: "#cbd5e1",
                  lineHeight: 1.4,
                  whiteSpace: "pre-wrap",
                }}
              >
                {entity.content}
              </div>
            )}
          </section>
        )}

        {/* 4. TEMPORAL (BI-TEMPORAL VISUALIZATION) */}
        <section>
          <div style={sectionTitleStyle}>BI-TEMPORAL BOUNDS</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {/* Business Time */}
            <div style={timeCardStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: "#38bdf8", fontSize: "0.72rem" }}>BUSINESS TIME (VALIDITY)</span>
                <span style={{ fontSize: "0.68rem", color: "#94a3b8" }}>Real-World Application</span>
              </div>
              <div style={{ fontSize: "0.72rem", color: "#e2e8f0", fontFamily: "monospace" }}>
                <span>{entity.valid_from}</span>
                <span style={{ color: "#64748b", margin: "0 6px" }}>→</span>
                <span>{entity.valid_until || "Indefinite / Active"}</span>
              </div>
            </div>

            {/* System Time */}
            <div style={timeCardStyle}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 600, color: "#a855f7", fontSize: "0.72rem" }}>SYSTEM TIME (AUDIT RECORD)</span>
                <span style={{ fontSize: "0.68rem", color: "#94a3b8" }}>Immutable Ledger</span>
              </div>
              <div style={{ fontSize: "0.72rem", color: "#e2e8f0", fontFamily: "monospace" }}>
                <span>{entity.recorded_from}</span>
                <span style={{ color: "#64748b", margin: "0 6px" }}>→</span>
                <span>{entity.recorded_until || "Current State"}</span>
              </div>
            </div>
          </div>
        </section>

        {/* 5. PROVENANCE & EVIDENCE GROUNDING */}
        <section>
          <div style={sectionTitleStyle}>GROUNDED EVIDENCE ({entity.evidence.length})</div>
          {entity.evidence.length === 0 ? (
            <div style={{ fontSize: "0.75rem", color: "#64748b" }}>No direct source evidence recorded for this entity.</div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {entity.evidence.map((ev, i) => (
                <div
                  key={ev.id || i}
                  style={{
                    backgroundColor: "#18202f",
                    borderRadius: 6,
                    border: "1px solid #334155",
                    padding: 10,
                  }}
                >
                  <div
                    style={{
                      fontSize: "0.7rem",
                      color: "#38bdf8",
                      fontFamily: "monospace",
                      marginBottom: 6,
                      wordBreak: "break-all",
                    }}
                  >
                    {ev.file_path && `${ev.file_path} `}
                    {ev.start_line > 0 && `(L${ev.start_line}-L${ev.end_line})`}
                  </div>

                  <blockquote
                    style={{
                      margin: 0,
                      padding: "6px 10px",
                      backgroundColor: "#0f172a",
                      borderLeft: "2px solid #0284c7",
                      fontSize: "0.75rem",
                      fontFamily: "monospace",
                      color: "#e2e8f0",
                      whiteSpace: "pre-wrap",
                      borderRadius: 3,
                    }}
                  >
                    "{ev.exact_quote}"
                  </blockquote>

                  {ev.commit_sha && (
                    <div style={{ fontSize: "0.65rem", color: "#64748b", marginTop: 6 }}>
                      Commit: <span style={{ fontFamily: "monospace", color: "#94a3b8" }}>{ev.commit_sha.slice(0, 7)}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 6. CAUSAL LINEAGE */}
        <section>
          <div style={sectionTitleStyle}>CAUSAL LINEAGE</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: "0.75rem" }}>
            <div style={causalRowStyle}>
              <span style={{ color: "#94a3b8" }}>Originating Event:</span>
              <button
                type="button"
                onClick={() => {
                  if (onSelectEvent) onSelectEvent(entity.originating_event_id);
                  setTab("event");
                }}
                style={linkButtonStyle}
                title="View in Timeline"
              >
                {entity.originating_event_id.slice(0, 16)}...
              </button>
            </div>

            {entity.last_transition_event_id && (
              <div style={causalRowStyle}>
                <span style={{ color: "#94a3b8" }}>Last Transition:</span>
                <span style={{ fontFamily: "monospace", color: "#cbd5e1" }}>
                  {entity.last_transition_event_id.slice(0, 16)}...
                </span>
              </div>
            )}

            {entity.superseded_by && (
              <div style={causalRowStyle}>
                <span style={{ color: "#f87171" }}>Superseded By:</span>
                <button
                  type="button"
                  onClick={() => onNavigateEntity && onNavigateEntity(entity.superseded_by!)}
                  style={{ ...linkButtonStyle, color: "#f87171" }}
                >
                  {entity.superseded_by}
                </button>
              </div>
            )}
          </div>
        </section>

        {/* 7. RELATION DENSITY */}
        <section>
          <div style={sectionTitleStyle}>RELATIONSHIP GRAPH REACH</div>
          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ ...metricBoxStyle, flex: 1 }}>
              <span style={metricLabelStyle}>Incoming Relations</span>
              <span style={{ color: "#f8fafc", fontWeight: 700, fontSize: "1rem" }}>
                {entity.incoming_relations_count}
              </span>
            </div>
            <div style={{ ...metricBoxStyle, flex: 1 }}>
              <span style={metricLabelStyle}>Outgoing Relations</span>
              <span style={{ color: "#f8fafc", fontWeight: 700, fontSize: "1rem" }}>
                {entity.outgoing_relations_count}
              </span>
            </div>
          </div>
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

const linkButtonStyle: React.CSSProperties = {
  background: "transparent",
  border: "none",
  color: "#38bdf8",
  cursor: "pointer",
  fontFamily: "monospace",
  fontSize: "0.75rem",
  textDecoration: "underline",
  padding: 0,
};

const tabBarStyle: React.CSSProperties = {
  display: "flex",
  borderBottom: "1px solid #334155",
  backgroundColor: "#090d16",
};

const tabBtnStyle: React.CSSProperties = {
  flex: 1,
  padding: "8px 12px",
  fontSize: "0.72rem",
  fontWeight: 700,
  border: "none",
  cursor: "pointer",
  backgroundColor: "transparent",
  transition: "all 0.15s ease",
};

