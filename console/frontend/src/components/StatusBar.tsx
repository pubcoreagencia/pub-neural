import { useEffect, useState } from "react";
import { NeuralAPI } from "../api/client";
import type { SystemStatusDTO } from "../api/types";

export function StatusBar() {
  const [status, setStatus] = useState<SystemStatusDTO | null>(null);

  useEffect(() => {
    NeuralAPI.getStatus()
      .then((data) => setStatus(data))
      .catch((err) => console.error("Failed to load status", err));
  }, []);

  if (!status) {
    return (
      <div style={{ padding: '4px 16px', background: '#333', color: 'white', fontSize: '0.8em', display: 'flex', justifyContent: 'space-between' }}>
        <span>PUB Neural Console</span>
        <span>Connecting...</span>
      </div>
    );
  }

  return (
    <div style={{ padding: '4px 16px', background: '#333', color: 'white', fontSize: '0.8em', display: 'flex', justifyContent: 'space-between' }}>
      <span>PUB Neural Console v0</span>
      <div style={{ display: 'flex', gap: 16 }}>
        <span>Status: {status.status}</span>
        <span>DB: {status.database_connected ? "Connected" : "Disconnected"}</span>
        <span>Trust Zone: {status.active_trust_zone || "None"}</span>
        <span>Role: {status.active_actor_role || "None"}</span>
      </div>
    </div>
  );
}
