import { useEffect, useState } from "react";
import { NeuralAPI } from "../api/client";
import type { EntityDetailDTO } from "../api/types";

interface InspectorPanelProps {
  entityId: string | null;
}

export function InspectorPanel({ entityId }: InspectorPanelProps) {
  const [entity, setEntity] = useState<EntityDetailDTO | null>(null);
  const [loading, setLoading] = useState(false);

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

  if (loading) {
    return <div style={{ padding: 16 }}>Loading...</div>;
  }

  if (!entity) {
    return <div style={{ padding: 16 }}>Select a node to inspect</div>;
  }

  return (
    <div style={{ padding: 16, borderLeft: '1px solid #ccc', height: '100%', boxSizing: 'border-box', overflowY: 'auto' }}>
      <h2>Inspector</h2>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div>
          <strong>Title:</strong> {entity.title}
        </div>
        <div>
          <strong>Type:</strong> {entity.entity_type}
        </div>
        <div>
          <strong>Promotion State:</strong> {entity.promotion_state}
        </div>
        <div>
          <strong>Conflict State:</strong> {entity.conflict_state}
        </div>
        <div>
          <strong>Trust Zone:</strong> {entity.trust_zone}
        </div>
        <div>
          <strong>Confidence:</strong> {entity.confidence_score}
        </div>
        {entity.summary && (
          <div>
            <strong>Summary:</strong>
            <p>{entity.summary}</p>
          </div>
        )}
        {entity.evidence && entity.evidence.length > 0 && (
          <div>
            <strong>Evidence:</strong>
            <ul style={{ paddingLeft: 16 }}>
              {entity.evidence.map((ev, i) => (
                <li key={i} style={{ marginBottom: 8 }}>
                  <pre style={{ fontSize: '0.8em', whiteSpace: 'pre-wrap', background: '#f5f5f5', padding: 8, borderRadius: 4 }}>
                    {ev.exact_quote}
                  </pre>
                  <div style={{ fontSize: '0.8em', color: '#666' }}>
                    {ev.file_path && ev.file_path} {ev.start_line && `L${ev.start_line}-L${ev.end_line}`}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}
