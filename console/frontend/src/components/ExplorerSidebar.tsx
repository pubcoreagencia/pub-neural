import { useState } from "react";
import { NeuralAPI } from "../api/client";
import type { SearchResponseDTO } from "../api/types";

interface ExplorerSidebarProps {
  onSelectEntity: (id: string) => void;
  selectedEntityId: string | null;
}

export function ExplorerSidebar({ onSelectEntity, selectedEntityId }: ExplorerSidebarProps) {
  const [query, setQuery] = useState("");
  const [searchResponse, setSearchResponse] = useState<SearchResponseDTO | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const response = await NeuralAPI.search(query.trim());
      setSearchResponse(response);
    } catch (err: any) {
      setError(err.message || "Search failed or backend unavailable.");
      setSearchResponse(null);
    } finally {
      setLoading(false);
    }
  };

  const results = searchResponse?.results || [];
  const status = searchResponse?.status;
  const abstention = searchResponse?.abstention_decision;

  return (
    <div
      style={{
        padding: "16px",
        backgroundColor: "#0f172a",
        borderRight: "1px solid #334155",
        display: "flex",
        flexDirection: "column",
        height: "100%",
        boxSizing: "border-box",
        overflowY: "auto",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
        <h2 style={{ fontSize: "1rem", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
          Neural Explorer
        </h2>
        <span style={{ fontSize: "0.65rem", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" }}>
          Read-Only V0
        </span>
      </div>

      <form onSubmit={handleSearch} style={{ display: "flex", gap: 6, marginBottom: 14 }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Hybrid search (e.g. Tokens, RRF)..."
          aria-label="Search neural entities"
          style={{
            flex: 1,
            padding: "8px 10px",
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: 6,
            color: "#f8fafc",
            fontSize: "0.8rem",
            outline: "none",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            padding: "8px 14px",
            backgroundColor: "#0284c7",
            color: "#ffffff",
            border: "none",
            borderRadius: 6,
            fontSize: "0.78rem",
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "..." : "Search"}
        </button>
      </form>

      {/* ERROR DISPLAY */}
      {error && (
        <div
          style={{
            backgroundColor: "rgba(239, 68, 68, 0.15)",
            border: "1px solid #ef4444",
            color: "#fca5a5",
            padding: "8px 10px",
            borderRadius: 6,
            fontSize: "0.75rem",
            marginBottom: 12,
          }}
        >
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* ABSTAINED DISPLAY */}
      {status === "ABSTAINED" && (
        <div
          style={{
            backgroundColor: "rgba(245, 158, 11, 0.15)",
            border: "1px solid #f59e0b",
            color: "#fcd34d",
            padding: "10px",
            borderRadius: 6,
            fontSize: "0.75rem",
            marginBottom: 12,
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 2 }}>Retrieval Abstained by Governance</div>
          <div>Reason: {abstention?.reason || "Confidence below retrieval threshold."}</div>
        </div>
      )}

      {/* NO MATCH DISPLAY */}
      {status === "NO_MATCH" && !loading && (
        <div
          style={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            color: "#94a3b8",
            padding: "12px",
            borderRadius: 6,
            fontSize: "0.75rem",
            textAlign: "center",
            marginBottom: 12,
          }}
        >
          No matching entities found for "{searchResponse?.query}".
        </div>
      )}

      {/* RESULTS LIST */}
      <ul
        style={{
          listStyle: "none",
          padding: 0,
          margin: 0,
          display: "flex",
          flexDirection: "column",
          gap: 8,
          flex: 1,
        }}
      >
        {results.map((r) => {
          const isSelected = r.target_id === selectedEntityId;
          return (
            <li
              key={r.target_id}
              tabIndex={0}
              role="button"
              onClick={() => onSelectEntity(r.target_id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  onSelectEntity(r.target_id);
                }
              }}
              style={{
                padding: 10,
                backgroundColor: isSelected ? "#1e293b" : "#18202f",
                border: `1px solid ${isSelected ? "#38bdf8" : "#334155"}`,
                borderRadius: 6,
                cursor: "pointer",
                boxShadow: isSelected ? "0 0 10px rgba(56, 189, 248, 0.25)" : "none",
                transition: "all 0.15s ease",
                outline: "none",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 6, marginBottom: 4 }}>
                <span
                  style={{
                    fontSize: "0.62rem",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    padding: "1px 5px",
                    borderRadius: 3,
                    backgroundColor: "#0284c7",
                    color: "#ffffff",
                  }}
                >
                  {r.target_type}
                </span>

                <span style={{ fontSize: "0.65rem", color: "#38bdf8", fontWeight: 600 }}>
                  RRF: {r.rrf_score.toFixed(4)}
                </span>
              </div>

              <div style={{ fontWeight: 600, color: "#f8fafc", fontSize: "0.82rem", marginBottom: 4 }}>
                {r.title}
              </div>

              {r.snippet && (
                <div
                  style={{
                    fontSize: "0.72rem",
                    color: "#94a3b8",
                    lineHeight: 1.3,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                  }}
                >
                  {r.snippet}
                </div>
              )}

              <div
                style={{
                  fontSize: "0.65rem",
                  color: "#64748b",
                  marginTop: 6,
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <span>TZ: {r.trust_zone}</span>
                {r.project_id && <span>Project: {r.project_id}</span>}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
