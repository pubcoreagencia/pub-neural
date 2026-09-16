import { useEffect, useState } from "react";
import { NeuralAPI } from "../api/client";
import type { OverviewResponseDTO, OverviewProjectDTO } from "../api/types";

interface OverviewViewProps {
  onSelectProjectForGraph?: (projectId: string) => void;
  onSelectProjectForTimeline?: (projectId: string) => void;
}

export function OverviewView({
  onSelectProjectForGraph,
  onSelectProjectForTimeline,
}: OverviewViewProps) {
  const [data, setData] = useState<OverviewResponseDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [windowDays, setWindowDays] = useState(14);

  const fetchOverview = () => {
    setLoading(true);
    setError(null);
    NeuralAPI.getOverview(windowDays)
      .then((res) => {
        setData(res);
      })
      .catch((err: any) => {
        setError(err.message || "Failed to load overview data");
      })
      .finally(() => {
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchOverview();
  }, [windowDays]);

  if (loading && !data) {
    return (
      <div style={{ padding: "32px", color: "#94a3b8", fontFamily: "monospace" }}>
        Loading Command Center Overview...
      </div>
    );
  }

  if (error && !data) {
    return (
      <div style={{ padding: "32px", color: "#f87171", fontFamily: "monospace" }}>
        Error loading Overview: {error}
        <div style={{ marginTop: "12px" }}>
          <button
            onClick={fetchOverview}
            style={{
              padding: "6px 12px",
              background: "#1e293b",
              border: "1px solid #334155",
              color: "#f1f5f9",
              borderRadius: "4px",
              cursor: "pointer",
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Extract exactly the ordered calendar days from daily_activity
  const calendarDays: string[] = [];
  if (data?.daily_activity) {
    for (const item of data.daily_activity) {
      if (!calendarDays.includes(item.day)) {
        calendarDays.push(item.day);
      }
    }
  }
  calendarDays.sort();

  // Helper to get count for a day/project
  const getDailyCount = (day: string, projectId: string): number => {
    const found = data?.daily_activity.find(
      (d) => d.day === day && d.project_id === projectId
    );
    return found ? found.observed_count : 0;
  };

  const getIntensityColor = (count: number): string => {
    if (count === 0) return "#1e293b";
    if (count < 3) return "#0e7490";
    if (count < 10) return "#0284c7";
    if (count < 25) return "#2563eb";
    return "#3b82f6";
  };

  return (
    <div
      style={{
        padding: "24px",
        overflowY: "auto",
        height: "100%",
        boxSizing: "border-box",
        backgroundColor: "#0b1120",
        color: "#f8fafc",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* Header controls & System/Projector Health */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px",
          borderBottom: "1px solid #1e293b",
          paddingBottom: "16px",
        }}
      >
        <div>
          <h1
            style={{
              margin: 0,
              fontSize: "18px",
              fontWeight: 700,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
              color: "#38bdf8",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <span>PUB NEURAL COMMAND CENTER</span>
            <span
              style={{
                fontSize: "10px",
                padding: "2px 6px",
                borderRadius: "4px",
                background: "#0369a1",
                color: "#e0f2fe",
              }}
            >
              V0.1
            </span>
          </h1>
          <div style={{ fontSize: "12px", color: "#64748b", marginTop: "4px" }}>
            Operational cockpit: observed projects, repository observations, active knowledge nodes
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          {/* Global System & Projector Health Badges */}
          <div style={{ display: "flex", gap: "8px" }}>
            <div
              style={{
                fontSize: "11px",
                padding: "4px 8px",
                borderRadius: "4px",
                backgroundColor:
                  data?.database_health === "HEALTHY"
                    ? "rgba(16, 185, 129, 0.15)"
                    : "rgba(239, 68, 68, 0.15)",
                color: data?.database_health === "HEALTHY" ? "#34d399" : "#f87171",
                border: `1px solid ${
                  data?.database_health === "HEALTHY"
                    ? "rgba(16, 185, 129, 0.3)"
                    : "rgba(239, 68, 68, 0.3)"
                }`,
                fontFamily: "monospace",
              }}
            >
              Database: {data?.database_health || "UNKNOWN"}
            </div>


            <div
              style={{
                fontSize: "11px",
                padding: "4px 8px",
                borderRadius: "4px",
                backgroundColor:
                  data?.projector_health === "HEALTHY"
                    ? "rgba(16, 185, 129, 0.15)"
                    : data?.projector_health === "DEGRADED"
                    ? "rgba(245, 158, 11, 0.15)"
                    : "rgba(239, 68, 68, 0.15)",
                color:
                  data?.projector_health === "HEALTHY"
                    ? "#34d399"
                    : data?.projector_health === "DEGRADED"
                    ? "#fcd34d"
                    : "#f87171",
                border: `1px solid ${
                  data?.projector_health === "HEALTHY"
                    ? "rgba(16, 185, 129, 0.3)"
                    : data?.projector_health === "DEGRADED"
                    ? "rgba(245, 158, 11, 0.3)"
                    : "rgba(239, 68, 68, 0.3)"
                }`,
                fontFamily: "monospace",
              }}
            >
              Projectors: {data?.projector_health || "UNKNOWN"}
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>Window:</span>
            <select
              value={windowDays}
              onChange={(e) => setWindowDays(Number(e.target.value))}
              style={{
                backgroundColor: "#1e293b",
                color: "#f8fafc",
                border: "1px solid #334155",
                borderRadius: "4px",
                padding: "4px 8px",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              <option value={7}>7 Days</option>
              <option value={14}>14 Days</option>
              <option value={30}>30 Days</option>
            </select>
            <button
              onClick={fetchOverview}
              style={{
                backgroundColor: "#1e293b",
                color: "#94a3b8",
                border: "1px solid #334155",
                borderRadius: "4px",
                padding: "4px 10px",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* SECTION 1: OBSERVED PROJECT CARDS */}
      <div style={{ marginBottom: "32px" }}>
        <div
          style={{
            fontSize: "13px",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#94a3b8",
            marginBottom: "12px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>Observed Projects ({data?.projects.length || 0})</span>
          <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
            • strictly factual sources (repository observations and active knowledge nodes)
          </span>
        </div>

        {data?.projects.length === 0 ? (
          <div
            style={{
              padding: "24px",
              backgroundColor: "#0f172a",
              borderRadius: "6px",
              border: "1px dashed #334155",
              color: "#64748b",
              fontSize: "13px",
            }}
          >
            No projects observed yet under current authorization scope.
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
              gap: "16px",
            }}
          >
            {data?.projects.map((proj: OverviewProjectDTO) => (
              <div
                key={proj.project_id}
                style={{
                  backgroundColor: "#0f172a",
                  border: "1px solid #1e293b",
                  borderRadius: "8px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontSize: "15px",
                        fontWeight: 600,
                        color: "#f1f5f9",
                        fontFamily: "monospace",
                      }}
                    >
                      {proj.project_id}
                    </div>
                    <div style={{ fontSize: "11px", color: "#64748b", marginTop: "2px" }}>
                      {proj.observed_repository_count > 0
                        ? `${proj.observed_repository_count} repository${proj.observed_repository_count === 1 ? "" : "ies"} observed`
                        : "No repository observations recorded"}
                    </div>
                  </div>

                  <div
                    style={{
                      fontSize: "11px",
                      color: "#94a3b8",
                      fontFamily: "monospace",
                    }}
                  >
                    Active Nodes: <strong style={{ color: "#38bdf8" }}>{proj.active_node_count}</strong>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr 1fr",
                    gap: "8px",
                    backgroundColor: "#1e293b",
                    padding: "10px",
                    borderRadius: "6px",
                  }}
                >
                  <div>
                    <div style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase" }}>
                      Today (UTC)
                    </div>
                    <div style={{ fontSize: "16px", fontWeight: 700, color: "#38bdf8" }}>
                      {proj.activity_today}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase" }}>
                      7D (UTC)
                    </div>
                    <div style={{ fontSize: "16px", fontWeight: 700, color: "#e2e8f0" }}>
                      {proj.activity_7d}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: "10px", color: "#94a3b8", textTransform: "uppercase" }}>
                      Total Obs
                    </div>
                    <div style={{ fontSize: "16px", fontWeight: 700, color: "#cbd5e1" }}>
                      {proj.observation_count}
                    </div>
                  </div>
                </div>

                {/* Secondary Meta */}
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: "11px",
                    color: "#64748b",
                  }}
                >
                  <span>
                    Last Observed:{" "}
                    {proj.last_observation_at
                      ? new Date(proj.last_observation_at).toUTCString().slice(0, 16)
                      : "UNKNOWN"}
                  </span>
                </div>

                {/* Action Drill-downs */}
                <div
                  style={{
                    display: "flex",
                    gap: "8px",
                    marginTop: "4px",
                    paddingTop: "8px",
                    borderTop: "1px solid #1e293b",
                  }}
                >
                  <button
                    onClick={() => onSelectProjectForGraph?.(proj.project_id)}
                    style={{
                      flex: 1,
                      backgroundColor: "#1e293b",
                      color: "#38bdf8",
                      border: "1px solid #334155",
                      borderRadius: "4px",
                      padding: "6px 8px",
                      fontSize: "11px",
                      cursor: "pointer",
                      fontWeight: 500,
                    }}
                  >
                    View Graph →
                  </button>
                  <button
                    onClick={() => onSelectProjectForTimeline?.(proj.project_id)}
                    style={{
                      flex: 1,
                      backgroundColor: "#1e293b",
                      color: "#94a3b8",
                      border: "1px solid #334155",
                      borderRadius: "4px",
                      padding: "6px 8px",
                      fontSize: "11px",
                      cursor: "pointer",
                      fontWeight: 500,
                    }}
                  >
                    Timeline →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* SECTION 2: DAILY ACTIVITY HEATMAP */}
      <div>
        <div
          style={{
            fontSize: "13px",
            fontWeight: 600,
            textTransform: "uppercase",
            letterSpacing: "0.05em",
            color: "#94a3b8",
            marginBottom: "12px",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span>Observed Repository Activity ({data?.window_days || windowDays} Calendar Days UTC)</span>
          <span style={{ fontSize: "11px", color: "#64748b", fontWeight: 400 }}>
            • 0 indicates 0 observations recorded (not project inactivity)
          </span>
        </div>

        {data?.projects.length === 0 || calendarDays.length === 0 ? (
          <div
            style={{
              padding: "24px",
              backgroundColor: "#0f172a",
              borderRadius: "6px",
              border: "1px dashed #334155",
              color: "#64748b",
              fontSize: "13px",
            }}
          >
            No daily activity observed within this window.
          </div>
        ) : (
          <div
            style={{
              backgroundColor: "#0f172a",
              border: "1px solid #1e293b",
              borderRadius: "8px",
              padding: "16px",
              overflowX: "auto",
            }}
          >
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: "12px",
              }}
            >
              <thead>
                <tr>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "8px 12px",
                      borderBottom: "1px solid #1e293b",
                      color: "#94a3b8",
                      width: "180px",
                    }}
                  >
                    Observed Project
                  </th>
                  {calendarDays.map((day) => (
                    <th
                      key={day}
                      style={{
                        padding: "8px 6px",
                        borderBottom: "1px solid #1e293b",
                        color: "#64748b",
                        fontSize: "10px",
                        textAlign: "center",
                        fontFamily: "monospace",
                      }}
                    >
                      {day.slice(5)}
                    </th>
                  ))}
                  <th
                    style={{
                      textAlign: "right",
                      padding: "8px 12px",
                      borderBottom: "1px solid #1e293b",
                      color: "#94a3b8",
                      width: "80px",
                    }}
                  >
                    Window Sum
                  </th>
                </tr>
              </thead>
              <tbody>
                {data?.projects.map((proj) => {
                  let sum = 0;

                  return (
                    <tr key={proj.project_id}>
                      <td
                        style={{
                          padding: "8px 12px",
                          borderBottom: "1px solid #1e293b",
                          fontFamily: "monospace",
                          color: "#f1f5f9",
                        }}
                      >
                        {proj.project_id}
                      </td>
                      {calendarDays.map((day) => {
                        const cnt = getDailyCount(day, proj.project_id);
                        sum += cnt;
                        return (
                          <td
                            key={day}
                            style={{
                              padding: "6px",
                              borderBottom: "1px solid #1e293b",
                              textAlign: "center",
                            }}
                          >
                            <div
                              title={`${proj.project_id} on ${day} (UTC): ${cnt} observations recorded`}
                              style={{
                                width: "24px",
                                height: "24px",
                                margin: "0 auto",
                                borderRadius: "3px",
                                backgroundColor: getIntensityColor(cnt),
                                color: cnt > 0 ? "#ffffff" : "#475569",
                                fontSize: "10px",
                                lineHeight: "24px",
                                fontFamily: "monospace",
                              }}
                            >
                              {cnt > 0 ? cnt : "0"}
                            </div>
                          </td>
                        );
                      })}
                      <td
                        style={{
                          padding: "8px 12px",
                          borderBottom: "1px solid #1e293b",
                          textAlign: "right",
                          fontFamily: "monospace",
                          fontWeight: 600,
                          color: sum > 0 ? "#38bdf8" : "#64748b",
                        }}
                      >
                        {sum}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
