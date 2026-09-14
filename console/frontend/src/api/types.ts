export interface GraphNodeDTO {
  id: string;
  entity_type: string;
  title: string;
  slug: string;
  summary: string | null;
  promotion_state: string;
  conflict_state: string;
  confidence_score: number;
  valid_from: string;
  valid_until: string | null;
  trust_zone: string;
  project_id: string | null;
  evidence_count: number;
}

export interface GraphEdgeDTO {
  id: string;
  source_id: string;
  target_id: string;
  relation_type: string;
  weight: number;
  is_bidirectional: boolean;
  trust_zone: string;
  is_active: boolean;
}

export interface GraphResponseDTO {
  nodes: GraphNodeDTO[];
  edges: GraphEdgeDTO[];
  center_node_id: string | null;
  hop_depth: number;
  total_nodes: number;
  total_edges: number;
}

export interface EntityDetailDTO {
  id: string;
  entity_type: string;
  title: string;
  slug: string;
  summary: string | null;
  content: string | null;
  promotion_state: string;
  promotion_reason: string | null;
  conflict_state: string;
  confidence_score: number;
  superseded_by: string | null;
  valid_from: string;
  valid_until: string | null;
  recorded_from: string;
  recorded_until: string | null;
  is_active: boolean;
  originating_event_id: string;
  last_transition_event_id: string | null;
  project_id: string | null;
  trust_zone: string;
  created_at: string;
  updated_at: string;
  evidence: any[];
  incoming_relations_count: number;
  outgoing_relations_count: number;
}

export interface SearchResultItemDTO {
  target_id: string;
  target_type: string;
  title: string;
  snippet: string;
  lexical_rank: number | null;
  dense_rank: number | null;
  rrf_score: number;
  trust_zone: string;
  project_id: string | null;
  originating_event_id: string;
}

export interface SearchResponseDTO {
  query: string;
  status: string;
  results: SearchResultItemDTO[];
  abstention_decision: any;
  lexical_count: number;
  dense_count: number;
}

export interface SystemStatusDTO {
  status: string;
  database_connected: boolean;
  postgresql_version: string | null;
  active_trust_zone: string | null;
  active_actor_role: string | null;
  projector_checkpoints: any[];
  capabilities: Record<string, string>;
  server_time: string;
}
