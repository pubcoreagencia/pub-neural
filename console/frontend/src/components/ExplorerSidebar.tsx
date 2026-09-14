import { useState } from "react";
import { NeuralAPI } from "../api/client";
import type { SearchResultItemDTO } from "../api/types";

interface ExplorerSidebarProps {
  onSelectEntity: (id: string) => void;
}

export function ExplorerSidebar({ onSelectEntity }: ExplorerSidebarProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResultItemDTO[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError("");
    try {
      const response = await NeuralAPI.search(query);
      setResults(response.results);
    } catch (err) {
      setError("Failed to search");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="explorer-sidebar" style={{ padding: 16, borderRight: '1px solid #ccc', display: 'flex', flexDirection: 'column', height: '100%', boxSizing: 'border-box', overflowY: 'auto' }}>
      <h2>Explorer</h2>
      <form onSubmit={handleSearch} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search entities..."
          style={{ flex: 1, padding: '4px 8px' }}
        />
        <button type="submit" disabled={loading}>
          Search
        </button>
      </form>
      {error && <div style={{ color: "red" }}>{error}</div>}
      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
        {results.map((r) => (
          <li
            key={r.target_id}
            onClick={() => onSelectEntity(r.target_id)}
            style={{
              padding: 12,
              border: "1px solid #ddd",
              cursor: "pointer",
              borderRadius: 4,
            }}
          >
            <div style={{ fontWeight: 'bold' }}>{r.title}</div>
            <div style={{ fontSize: '0.8em', color: '#666', marginTop: 4 }}>Type: {r.target_type}</div>
            <div style={{ fontSize: '0.8em', color: '#666' }}>Trust Zone: {r.trust_zone}</div>
          </li>
        ))}
        {results.length === 0 && !loading && !error && <div>No results</div>}
        {loading && <div>Searching...</div>}
      </ul>
    </div>
  );
}
