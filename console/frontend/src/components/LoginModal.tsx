import { useState, type FormEvent } from "react";
import { NeuralAPI } from "../api/client";
import type { AuthResponseDTO } from "../api/types";

interface LoginModalProps {
  onLoginSuccess: (session: AuthResponseDTO) => void;
  onClose?: () => void;
}

export function LoginModal({ onLoginSuccess, onClose }: LoginModalProps) {
  const [actorId, setActorId] = useState("actor:auditor:console-operator");
  const [secret, setSecret] = useState("");
  const [trustZone, setTrustZone] = useState("tz_internal_holding");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!actorId.trim() || !secret.trim()) {
      setError("Actor ID and Machine Secret are required.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const session = await NeuralAPI.login({
        actorId: actorId.trim(),
        secret: secret.trim(),
        trustZone: trustZone.trim(),
      });
      onLoginSuccess(session);
    } catch (err: any) {
      setError(err.message || "Authentication failed. Check credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(15, 23, 42, 0.85)",
        backdropFilter: "blur(4px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "420px",
          backgroundColor: "#0b1329",
          border: "1px solid #1e293b",
          borderRadius: "8px",
          boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
          padding: "24px",
          color: "#f8fafc",
          fontFamily: "system-ui, -apple-system, sans-serif",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: "1.1rem", fontWeight: 700, color: "#38bdf8", letterSpacing: "0.02em" }}>
              PUB NEURAL AUTHENTICATION
            </h2>
            <p style={{ margin: "4px 0 0 0", fontSize: "0.75rem", color: "#64748b" }}>
              Authenticate with an active trusted operator actor
            </p>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: "transparent",
                border: "none",
                color: "#64748b",
                fontSize: "1.2rem",
                cursor: "pointer",
              }}
            >
              ✕
            </button>
          )}
        </div>

        {error && (
          <div
            style={{
              padding: "10px 12px",
              backgroundColor: "rgba(220, 38, 38, 0.2)",
              border: "1px solid #ef4444",
              borderRadius: "4px",
              color: "#fca5a5",
              fontSize: "0.78rem",
              marginBottom: "16px",
            }}
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          <div>
            <label style={{ display: "block", fontSize: "0.72rem", color: "#94a3b8", marginBottom: "4px", fontWeight: 600 }}>
              ACTOR ID
            </label>
            <input
              type="text"
              value={actorId}
              onChange={(e) => setActorId(e.target.value)}
              placeholder="actor:auditor:..."
              style={{
                width: "100%",
                padding: "8px 10px",
                backgroundColor: "#030712",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: "#f8fafc",
                fontSize: "0.82rem",
                boxSizing: "border-box",
                outline: "none",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.72rem", color: "#94a3b8", marginBottom: "4px", fontWeight: 600 }}>
              MACHINE SECRET
            </label>
            <input
              type="password"
              value={secret}
              onChange={(e) => setSecret(e.target.value)}
              placeholder="Enter high-entropy machine secret"
              style={{
                width: "100%",
                padding: "8px 10px",
                backgroundColor: "#030712",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: "#f8fafc",
                fontSize: "0.82rem",
                boxSizing: "border-box",
                outline: "none",
              }}
            />
          </div>

          <div>
            <label style={{ display: "block", fontSize: "0.72rem", color: "#94a3b8", marginBottom: "4px", fontWeight: 600 }}>
              REQUESTED TRUST ZONE
            </label>
            <select
              value={trustZone}
              onChange={(e) => setTrustZone(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 10px",
                backgroundColor: "#030712",
                border: "1px solid #334155",
                borderRadius: "4px",
                color: "#f8fafc",
                fontSize: "0.82rem",
                boxSizing: "border-box",
                outline: "none",
              }}
            >
              <option value="tz_internal_holding">tz_internal_holding</option>
              <option value="tz_client_facing">tz_client_facing</option>
              <option value="tz_public">tz_public</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              marginTop: "8px",
              padding: "10px",
              backgroundColor: loading ? "#075985" : "#0284c7",
              color: "#ffffff",
              border: "none",
              borderRadius: "4px",
              fontSize: "0.82rem",
              fontWeight: 600,
              cursor: loading ? "wait" : "pointer",
              transition: "background-color 0.2s",
            }}
          >
            {loading ? "Authenticating Session..." : "Establish Authorized Session"}
          </button>
        </form>

        <div style={{ marginTop: "16px", borderTop: "1px solid #1e293b", paddingTop: "12px", fontSize: "0.68rem", color: "#64748b", textAlign: "center" }}>
          Protected by PostgreSQL RLS + Cryptographic Token Hash Validation
        </div>
      </div>
    </div>
  );
}
