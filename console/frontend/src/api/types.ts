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

export interface EvidenceLocatorDTO {
  id: string;
  source_id: string;
  repository: string | null;
  commit_sha: string | null;
  file_path: string | null;
  start_line: number;
  end_line: number;
  exact_quote: string;
  confidence: number;
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
  evidence: EvidenceLocatorDTO[];
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

export interface AbstentionDecisionDTO {
  accepted: boolean;
  reason: string | null;
  top_dense_similarity: number | null;
  top_rrf_score: number | null;
  lexical_candidate_count: number;
  dense_candidate_count: number;
}

export interface SearchResponseDTO {
  query: string;
  status: "SUCCESS" | "ABSTAINED" | "NO_MATCH";
  results: SearchResultItemDTO[];
  abstention_decision: AbstentionDecisionDTO;
  lexical_count: number;
  dense_count: number;
}

export interface SystemStatusDTO {
  status: "HEALTHY" | "DEGRADED" | "UNAVAILABLE" | "ERROR" | string;
  database_connected: boolean;
  postgresql_version: string | null;
  active_trust_zone: string | null;
  active_actor_role: string | null;
  projector_checkpoints: Array<{
    projector_name: string;
    last_processed_global_sequence: number;
    status: string;
    last_checkpoint_at: string;
    error_detail?: string | null;
  }>;
  capabilities: Record<string, string>;
  server_time: string;
}

export interface EventItemDTO {
  id: string;
  global_sequence: number;
  event_type: string;
  event_version: number;
  producer_version: string;
  stream_id: string;
  stream_version: number;
  actor_id: string;
  actor_role: string;
  recorded_at: string;
}

export interface EventDetailDTO {
  id: string;
  global_sequence: number;
  event_type: string;
  event_version: number;
  payload_schema_version: number;
  producer_version: string;
  stream_id: string;
  stream_version: number;
  actor_id: string;
  actor_role: string;
  payload: Record<string, any>;
  signature: string | null;
  recorded_at: string;
  parent_event_ids: string[];
}

export interface EventListResponseDTO {
  events: EventItemDTO[];
  total_returned: number;
  limit: number;
  offset: number;
}

export interface LatestSignalDTO {
  type: "REPOSITORY_OBSERVED" | "TASK_EXPERIENCE_RECORDED" | string;
  timestamp: string;
  summary: string;
  source: string;
  locator: string;
}

export interface OverviewProjectDTO {
  project_id: string;
  observed_repository_count: number;
  observation_count: number;
  activity_today: number;
  activity_7d: number;
  last_observation_at: string | null;
  active_node_count: number;
  project_state: string;
  blocked_nodes_count: number;
  latest_signal: LatestSignalDTO | null;
}

export interface DailyActivityBucketDTO {
  day: string;
  project_id: string;
  observed_count: number;
}

export interface OverviewResponseDTO {
  generated_at: string;
  window_days: number;
  database_health: string;
  projector_health: string;
  projects: OverviewProjectDTO[];
  daily_activity: DailyActivityBucketDTO[];
}

