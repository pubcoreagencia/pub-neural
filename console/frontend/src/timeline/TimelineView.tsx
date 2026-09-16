import { useEffect, useState } from "react";
import { NeuralAPI } from "../api/client";
import type { EventItemDTO } from "../api/types";

interface TimelineViewProps {
  selectedEventId: string | null;
  onSelectEvent: (eventId: string) => void;
  onNavigateEntity?: (entityId: string) => void;
  initialStreamFilter?: string;
}

export function TimelineView({
  selectedEventId,
  onSelectEvent,
  onNavigateEntity,
  initialStreamFilter = "",
}: TimelineViewProps) {
  const [events, setEvents] = useState<EventItemDTO[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & pagination
  const [eventTypeFilter, setEventTypeFilter] = useState("");
  const [streamIdFilter, setStreamIdFilter] = useState(initialStreamFilter);

  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);

  const fetchEvents = () => {
    setLoading(true);
    setError(null);
    NeuralAPI.getEvents({
      limit,
      offset,
      streamId: streamIdFilter.trim() || undefined,
      eventType: eventTypeFilter.trim() || undefined,
    })
      .then((data) => {
        setEvents(data.events || []);
      })
      .catch((err: any) => {
        setError(err.message || "Failed to fetch timeline events.");
        setEvents([]);
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchEvents();
  }, [limit, offset]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setOffset(0);
    fetchEvents();
  };

  const handleClearFilters = () => {
    setEventTypeFilter("");
    setStreamIdFilter("");
    setOffset(0);
  };

  // Helper to extract entity ID from stream_id if it follows entity convention
  const getEntityFromStream = (streamId: string): string | null => {
    if (streamId.startsWith("entity:")) {
      return streamId.replace(/^entity:/, "");
    }
    return null;
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "#0b0f19",
        color: "#f8fafc",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* 1. TIMELINE TOP BAR / FILTER CONTROLS */}
      <div
        style={{
          padding: "12px 16px",
          backgroundColor: "#0f172a",
          borderBottom: "1px solid #1e293b",
          display: "flex",
          flexWrap: "wrap",
          alignItems: "center",
          gap: 10,
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#f8fafc" }}>
            ◷ Event Ledger Timeline
          </span>
          <span
            style={{
              fontSize: "0.68rem",
              padding: "2px 6px",
              backgroundColor: "#1e293b",
              borderRadius: 4,
              color: "#a855f7",
              border: "1px solid #9333ea",
              fontWeight: 600,
            }}
          >
            Append-Only
          </span>
        </div>

        <form
          onSubmit={handleFilterSubmit}
          style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}
        >
          <input
            type="text"
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            placeholder="Filter Event Type..."
            aria-label="Filter Event Type"
            style={filterInputStyle}
          />
          <input
            type="text"
            value={streamIdFilter}
            onChange={(e) => setStreamIdFilter(e.target.value)}
            placeholder="Filter Stream ID..."
            aria-label="Filter Stream ID"
            style={filterInputStyle}
          />

          <select
            value={limit}
            onChange={(e) => {
              setLimit(Number(e.target.value));
              setOffset(0);
            }}
            aria-label="Select Limit"
            style={selectStyle}
          >
            <option value={25}>25 / page</option>
            <option value={50}>50 / page</option>
            <option value={100}>100 / page</option>
          </select>

          <button type="submit" style={actionBtnStyle}>
            Apply
          </button>
          {(eventTypeFilter || streamIdFilter) && (
            <button
              type="button"
              onClick={handleClearFilters}
              style={{ ...actionBtnStyle, backgroundColor: "#334155" }}
            >
              Clear
            </button>
          )}
          <button
            type="button"
            onClick={fetchEvents}
            title="Refresh Timeline"
            style={{ ...actionBtnStyle, backgroundColor: "#1e293b", border: "1px solid #475569" }}
          >
            ↻
          </button>
        </form>
      </div>

      {/* 2. TIMELINE FEED CONTAINER */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px 20px",
        }}
      >
        {loading && events.length === 0 && (
          <div style={{ textAlign: "center", padding: "40px 0", color: "#38bdf8", fontSize: "0.85rem" }}>
            Loading timeline events from canonical ledger...
          </div>
        )}

        {error && (
          <div
            style={{
              padding: "14px",
              backgroundColor: "rgba(239, 68, 68, 0.15)",
              border: "1px solid #ef4444",
              borderRadius: 6,
              color: "#fca5a5",
              fontSize: "0.82rem",
              marginBottom: 16,
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}

        {!loading && !error && events.length === 0 && (
          <div
            style={{
              padding: "48px 16px",
              textAlign: "center",
              color: "#64748b",
              fontSize: "0.85rem",
            }}
          >
            No events found matching current criteria.
          </div>
        )}

        {/* EVENT LIST */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {events.map((ev) => {
            const isSelected = selectedEventId === ev.id;
            const entityRef = getEntityFromStream(ev.stream_id);

            return (
              <div
                key={ev.id}
                onClick={() => onSelectEvent(ev.id)}
                style={{
                  backgroundColor: isSelected ? "#1e293b" : "#131b2e",
                  border: isSelected ? "1px solid #38bdf8" : "1px solid #1e293b",
                  borderRadius: 8,
                  padding: "12px 14px",
                  cursor: "pointer",
                  transition: "all 0.15s ease-in-out",
                  boxShadow: isSelected ? "0 0 10px rgba(56, 189, 248, 0.2)" : "none",
                }}
              >
                {/* TOP ROW: GLOBAL SEQUENCE, EVENT TYPE, ACTOR */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 8,
                    marginBottom: 6,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span
                      style={{
                        fontSize: "0.68rem",
                        fontFamily: "monospace",
                        color: "#94a3b8",
                        backgroundColor: "#0f172a",
                        padding: "2px 6px",
                        borderRadius: 4,
                      }}
                    >
                      #{ev.global_sequence}
                    </span>
                    <span
                      style={{
                        fontSize: "0.72rem",
                        fontWeight: 700,
                        color: "#a855f7",
                        textTransform: "uppercase",
                      }}
                    >
                      {ev.event_type}
                    </span>
                    <span
                      style={{
                        fontSize: "0.65rem",
                        color: "#64748b",
                        backgroundColor: "#1e293b",
                        padding: "1px 6px",
                        borderRadius: 3,
                      }}
                    >
                      v{ev.event_version}
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span
                      style={{
                        fontSize: "0.68rem",
                        color: "#34d399",
                        fontWeight: 600,
                      }}
                    >
                      {ev.actor_role}
                    </span>
                    <span
                      style={{
                        fontSize: "0.65rem",
                        color: "#94a3b8",
                        fontFamily: "monospace",
                      }}
                    >
                      ({ev.actor_id})
                    </span>
                  </div>
                </div>

                {/* MIDDLE ROW: STREAM & TIMESTAMPS */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    fontSize: "0.72rem",
                    color: "#94a3b8",
                    marginTop: 4,
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span>Stream:</span>
                    <span style={{ fontFamily: "monospace", color: "#cbd5e1" }}>
                      {ev.stream_id} (v{ev.stream_version})
                    </span>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span style={{ color: "#64748b", fontSize: "0.68rem" }}>EVENT TIME:</span>
                    <span style={{ fontFamily: "monospace", color: "#f8fafc" }}>
                      {ev.recorded_at}
                    </span>
                  </div>
                </div>

                {/* BOTTOM ROW: ACTIONS & ENTITY NAV */}
                {entityRef && onNavigateEntity && (
                  <div
                    style={{
                      marginTop: 8,
                      paddingTop: 8,
                      borderTop: "1px solid #1e293b",
                      display: "flex",
                      justifyContent: "flex-end",
                    }}
                  >
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onNavigateEntity(entityRef);
                      }}
                      style={{
                        background: "transparent",
                        border: "1px solid #0284c7",
                        color: "#38bdf8",
                        borderRadius: 4,
                        padding: "2px 8px",
                        fontSize: "0.68rem",
                        cursor: "pointer",
                        fontWeight: 600,
                      }}
                    >
                      View Entity in Graph →
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. PAGINATION FOOTER */}
      <div
        style={{
          padding: "8px 16px",
          backgroundColor: "#0f172a",
          borderTop: "1px solid #1e293b",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: "0.75rem",
          color: "#94a3b8",
        }}
      >
        <span>
          Showing {events.length} events (Offset: {offset})
        </span>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            type="button"
            disabled={offset === 0 || loading}
            onClick={() => setOffset((prev) => Math.max(0, prev - limit))}
            style={{
              ...actionBtnStyle,
              backgroundColor: offset === 0 ? "#1e293b" : "#334155",
              color: offset === 0 ? "#475569" : "#ffffff",
              cursor: offset === 0 ? "not-allowed" : "pointer",
            }}
          >
            ← Previous
          </button>
          <button
            type="button"
            disabled={events.length < limit || loading}
            onClick={() => setOffset((prev) => prev + limit)}
            style={{
              ...actionBtnStyle,
              backgroundColor: events.length < limit ? "#1e293b" : "#334155",
              color: events.length < limit ? "#475569" : "#ffffff",
              cursor: events.length < limit ? "not-allowed" : "pointer",
            }}
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}

// Styles
const filterInputStyle: React.CSSProperties = {
  padding: "4px 8px",
  backgroundColor: "#1e293b",
  border: "1px solid #334155",
  borderRadius: 4,
  color: "#f8fafc",
  fontSize: "0.72rem",
  outline: "none",
};

const selectStyle: React.CSSProperties = {
  padding: "4px 8px",
  backgroundColor: "#1e293b",
  border: "1px solid #334155",
  borderRadius: 4,
  color: "#f8fafc",
  fontSize: "0.72rem",
  outline: "none",
  cursor: "pointer",
};

const actionBtnStyle: React.CSSProperties = {
  padding: "4px 10px",
  backgroundColor: "#0284c7",
  color: "#ffffff",
  border: "none",
  borderRadius: 4,
  fontSize: "0.72rem",
  fontWeight: 600,
  cursor: "pointer",
};
