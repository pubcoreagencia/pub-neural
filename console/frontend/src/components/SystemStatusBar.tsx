import { useEffect, useState } from "react";
import { NeuralAPI } from "../api/client";
import type { SystemStatusDTO } from "../api/types";

interface SystemStatusBarProps {
  viewMode: "overview" | "graph" | "timeline";
  onViewModeChange: (mode: "overview" | "graph" | "timeline") => void;
}


export function SystemStatusBar({ viewMode, onViewModeChange }: SystemStatusBarProps) {
  const [status, setStatus] = useState<SystemStatusDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCapabilities, setShowCapabilities] = useState(false);

  const fetchStatus = () => {
    setLoading(true);
    setError(null);
    NeuralAPI.getStatus()
      .then((data) => {
        setStatus(data);
      })
      .catch((err: any) => {
        setError(err.message || "Failed to load system status");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchStatus();
    // Poll every 30 seconds for live health check
    const timer = setInterval(fetchStatus, 30000);
    return () => clearInterval(timer);
  }, []);

  // Compute status semantic state
  const getSemanticStatus = (): { label: string; color: string; bg: string } => {
    if (error) {
      return { label: "ERROR", color: "#fca5a5", bg: "rgba(220, 38, 38, 0.3)" };
    }
    if (!status) {
      return { label: "CONNECTING", color: "#93c5fd", bg: "rgba(30, 58, 138, 0.3)" };
    }
    if (!status.database_connected) {
      return { label: "UNAVAILABLE", color: "#f87171", bg: "rgba(239, 68, 68, 0.25)" };
    }

    const hasCheckpointErrors = status.projector_checkpoints?.some(
      (cp) => cp.status === "ERROR" || Boolean(cp.error_detail)
    );
    if (hasCheckpointErrors || status.status === "DEGRADED") {
      return { label: "DEGRADED", color: "#fcd34d", bg: "rgba(245, 158, 11, 0.25)" };
    }

    if (status.status === "HEALTHY") {
      return { label: "HEALTHY", color: "#34d399", bg: "rgba(16, 185, 129, 0.25)" };
    }

    return { label: status.status || "UNKNOWN", color: "#cbd5e1", bg: "rgba(100, 116, 139, 0.25)" };
  };

  const semantic = getSemanticStatus();

  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "8px 16px",
        backgroundColor: "#090d16",
        borderBottom: "1px solid #1e293b",
        color: "#f8fafc",
        fontSize: "0.78rem",
        zIndex: 50,
        position: "relative",
      }}
    >
      {/* 1. BRAND & VIEW MODE SWITCH */}
      <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontWeight: 800, fontSize: "0.9rem", letterSpacing: "0.04em", color: "#38bdf8" }}>
            PUB NEURAL
          </span>
          <span style={{ fontSize: "0.68rem", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Console V0
          </span>
        </div>

        {/* View Mode Toggle */}
        <div
          style={{
            display: "flex",
            backgroundColor: "#1e293b",
            borderRadius: 6,
            padding: 2,
            border: "1px solid #334155",
          }}
        >
          <button
            type="button"
            onClick={() => onViewModeChange("overview")}
            style={{
              padding: "4px 12px",
              borderRadius: 4,
              border: "none",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: "pointer",
              backgroundColor: viewMode === "overview" ? "#0369a1" : "transparent",
              color: viewMode === "overview" ? "#ffffff" : "#94a3b8",
              transition: "all 0.15s ease",
            }}
          >
            ⌘ Overview
          </button>
          <button
            type="button"
            onClick={() => onViewModeChange("graph")}
            style={{
              padding: "4px 12px",
              borderRadius: 4,
              border: "none",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: "pointer",
              backgroundColor: viewMode === "graph" ? "#0284c7" : "transparent",
              color: viewMode === "graph" ? "#ffffff" : "#94a3b8",
              transition: "all 0.15s ease",
            }}
          >
            ✦ Knowledge Graph
          </button>

          <button
            type="button"
            onClick={() => onViewModeChange("timeline")}
            style={{
              padding: "4px 12px",
              borderRadius: 4,
              border: "none",
              fontSize: "0.72rem",
              fontWeight: 600,
              cursor: "pointer",
              backgroundColor: viewMode === "timeline" ? "#a855f7" : "transparent",
              color: viewMode === "timeline" ? "#ffffff" : "#94a3b8",
              transition: "all 0.15s ease",
            }}
          >
            ◷ Event Timeline
          </button>
        </div>
      </div>

      {/* 2. OPERATIONAL STATUS BADGES */}
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        {/* Semantic Status Badge */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            padding: "2px 8px",
            borderRadius: 4,
            backgroundColor: semantic.bg,
            border: `1px solid ${semantic.color}`,
          }}
        >
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              backgroundColor: semantic.color,
            }}
          />
          <span style={{ fontWeight: 700, fontSize: "0.68rem", color: semantic.color }}>
            {semantic.label}
          </span>
        </div>

        {/* PostgreSQL Version */}
        {status?.postgresql_version && (
          <div
            style={{
              fontSize: "0.7rem",
              color: "#94a3b8",
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
            title={status.postgresql_version}
          >
            <span style={{ color: "#64748b" }}>PG:</span>
            <span style={{ fontFamily: "monospace", color: "#cbd5e1" }}>
              {status.postgresql_version.split(" ")[0]} {status.postgresql_version.split(" ")[1]}
            </span>
          </div>
        )}

        {/* Active Trust Zone & Role */}
        {status?.active_trust_zone && (
          <div style={{ fontSize: "0.7rem", color: "#94a3b8", display: "flex", gap: 4 }}>
            <span style={{ color: "#64748b" }}>Zone:</span>
            <span style={{ color: "#38bdf8", fontFamily: "monospace" }}>
              {status.active_trust_zone}
            </span>
          </div>
        )}

        {status?.active_actor_role && (
          <div style={{ fontSize: "0.7rem", color: "#94a3b8", display: "flex", gap: 4 }}>
            <span style={{ color: "#64748b" }}>Role:</span>
            <span style={{ color: "#34d399", fontWeight: 600 }}>
              {status.active_actor_role}
            </span>
          </div>
        )}

        {/* Checkpoint Badge */}
        {status?.projector_checkpoints && (
          <div
            style={{
              fontSize: "0.68rem",
              color: "#94a3b8",
              backgroundColor: "#18202f",
              padding: "2px 6px",
              borderRadius: 4,
              border: "1px solid #334155",
            }}
          >
            Checkpoints: <span style={{ color: "#f8fafc" }}>{status.projector_checkpoints.length}</span>
          </div>
        )}

        {/* Capabilities Dropdown Toggle */}
        {status?.capabilities && (
          <div style={{ position: "relative" }}>
            <button
              type="button"
              onClick={() => setShowCapabilities(!showCapabilities)}
              style={{
                background: "transparent",
                border: "1px solid #475569",
                color: "#94a3b8",
                borderRadius: 4,
                padding: "2px 8px",
                fontSize: "0.68rem",
                cursor: "pointer",
              }}
            >
              Capabilities ▾
            </button>

            {showCapabilities && (
              <div
                style={{
                  position: "absolute",
                  right: 0,
                  top: 26,
                  width: 320,
                  backgroundColor: "#0f172a",
                  border: "1px solid #334155",
                  borderRadius: 6,
                  padding: 12,
                  boxShadow: "0 10px 25px rgba(0,0,0,0.5)",
                  zIndex: 100,
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 8,
                    borderBottom: "1px solid #1e293b",
                    paddingBottom: 4,
                  }}
                >
                  <span style={{ fontWeight: 700, fontSize: "0.72rem", color: "#f8fafc" }}>
                    VERIFIED CAPABILITIES
                  </span>
                  <button
                    type="button"
                    onClick={() => setShowCapabilities(false)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "#94a3b8",
                      cursor: "pointer",
                    }}
                  >
                    ✕
                  </button>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 6, maxHeight: 220, overflowY: "auto" }}>
                  {Object.entries(status.capabilities).map(([key, val]) => (
                    <div key={key} style={{ fontSize: "0.68rem", display: "flex", justifyContent: "space-between" }}>
                      <span style={{ color: "#94a3b8", fontFamily: "monospace" }}>{key}</span>
                      <span
                        style={{
                          fontWeight: 600,
                          color: val.startsWith("ACTIVE") ? "#34d399" : "#64748b",
                        }}
                      >
                        {val.split(" ")[0]}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Refresh button */}
        <button
          type="button"
          onClick={fetchStatus}
          disabled={loading}
          title="Refresh System Status"
          style={{
            background: "transparent",
            border: "1px solid #334155",
            color: "#94a3b8",
            borderRadius: 4,
            padding: "2px 6px",
            fontSize: "0.68rem",
            cursor: loading ? "wait" : "pointer",
          }}
        >
          {loading ? "..." : "↻"}
        </button>
      </div>
    </header>
  );
}
