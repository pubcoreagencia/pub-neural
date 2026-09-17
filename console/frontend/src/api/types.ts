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
  association_status?: "CONFIRMED" | "PROPOSED" | "UNCLASSIFIED" | string | null;
  classification_source?: string | null;
  classification_confidence?: number | null;
  classification_reason?: string | null;
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
  repository?: string | null;
  event_id?: string | null;
  project_id?: string | null;
}

export interface ActivitySignalDTO {
  id: string;
  project_id?: string | null;
  project_display_name?: string | null;
  repository_id?: string | null;
  repository_name?: string | null;
  activity_type: string;
  timestamp: string;
  source: string;
  summary: string;
  locator: string;
  evidence_preview?: Record<string, any> | null;
  event_id?: string | null;
}

export interface ActivityListResponseDTO {
  window_days: number;
  total_signals: number;
  projects_with_activity_today: number;
  projects_with_activity_7d: number;
  signals: ActivitySignalDTO[];
}

export interface ProjectRegistryItemDTO {
  id: string;
  repository_full_name: string;
  repository_name: string;
  display_name: string;
  description: string | null;
  category: string;
  lifecycle_status: string;
  is_active: boolean;
  is_archived: boolean;
  is_private: boolean;
  monitoring_enabled: boolean;
  strategic_priority: string;
  github_url: string | null;
  created_at: string;
  updated_at: string;
  last_discovered_at: string;
}

export interface ProjectRegistryListDTO {
  total_count: number;
  projects: ProjectRegistryItemDTO[];
}

export interface ProjectRepositoryAssociationDTO {
  project_id: string;
  repository_id: string;
  repository_name: string;
  display_name: string;
  category: string;
  relationship_type: string;
  is_primary: boolean;
  association_status: "CONFIRMED" | "PROPOSED" | "UNCLASSIFIED" | string;
  classification_source: string;
  classification_confidence: number;
  classification_reason?: string | null;
  github_url?: string | null;
  classified_at?: string | null;
  classified_by?: string | null;
}

export interface HoldingProjectItemDTO {
  id: string;
  slug: string;
  display_name: string;
  description?: string | null;
  project_type: string;
  lifecycle_status: string;
  is_active: boolean;
  is_archived: boolean;
  strategic_priority: string;
  owner_scope: string;
  repositories_count: number;
  confirmed_repositories_count: number;
  proposed_repositories_count: number;
  active_knowledge_nodes_count: number;
  recent_observations_7d: number;
  repositories: ProjectRepositoryAssociationDTO[];
  created_at: string;
  updated_at: string;
  ontology_status: "CONFIRMED" | "PROPOSED" | "UNKNOWN" | string;
  ontology_source: string;
  ontology_confidence: number;
  ontology_reason?: string | null;
  ontology_verified_at?: string | null;
  ontology_verified_by?: string | null;
}

export interface HoldingProjectListDTO {
  total_projects: number;
  projects: HoldingProjectItemDTO[];
}

export interface ExecutiveSummaryDTO {
  total_holding_projects?: number;
  total_repositories?: number;
  multi_repo_projects_count?: number;
  unclassified_repositories_count?: number;
  confirmed_associations_count?: number;
  proposed_associations_count?: number;
  confirmed_projects_count?: number;
  proposed_projects_count?: number;
  unknown_projects_count?: number;
  projects_with_activity_today_count?: number;
  projects_with_activity_7d_count?: number;
  total_projects?: number;
  active_projects: number;
  monitored_repositories: number;
  recent_observations_7d: number;
  events_today: number;
  candidate_knowledge_count: number;
  adopted_knowledge_count: number;
  neural_health: string;
}

export interface GovernancePendingProjectDTO {
  id: string;
  slug: string;
  display_name: string;
  description?: string | null;
  project_type: string;
  lifecycle_status: string;
  strategic_priority: string;
  ontology_status: string;
  ontology_source: string;
  ontology_confidence: number;
  ontology_reason?: string | null;
  repositories_count: number;
}

export interface GovernancePendingAssociationDTO {
  project_id: string;
  project_display_name: string;
  repository_id: string;
  repository_name: string;
  repository_display_name: string;
  relationship_type: string;
  is_primary: boolean;
  association_status: string;
  classification_source: string;
  classification_confidence: number;
  classification_reason?: string | null;
  classified_at?: string | null;
  classified_by?: string | null;
}

export interface GovernanceOntologyQueuesDTO {
  pending_projects_count: number;
  pending_projects: GovernancePendingProjectDTO[];
  pending_associations_count: number;
  pending_associations: GovernancePendingAssociationDTO[];
  unclassified_repositories_count: number;
  unclassified_repositories: ProjectRegistryItemDTO[];
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
  operational_activity_state?: "ATIVIDADE_HOJE" | "ATIVIDADE_RECENTE" | "SEM_ATIVIDADE_NO_PERIODO" | "DADOS_INSUFICIENTES" | string;
  signals_today?: number;
  signals_7d?: number;
  blocked_nodes_count: number;
  latest_signal: LatestSignalDTO | null;
  display_name?: string;
  description?: string;
  category?: string;
  lifecycle_status?: string;
  is_active?: boolean;
  is_archived?: boolean;
  monitoring_enabled?: boolean;
  github_url?: string | null;
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
  executive_summary?: ExecutiveSummaryDTO | null;
  holding_projects?: HoldingProjectItemDTO[] | null;
}

export interface CandidateReviewDTO {
  id: string;
  entity_type: string;
  title: string;
  summary: string | null;
  content: string | null;
  promotion_state: string;
  promotion_reason: string | null;
  conflict_state: string;
  scope: string;
  project_id: string | null;
  trust_zone: string;
  originating_event_id: string;
  originating_event_type: string | null;
  proposed_by_actor_id: string | null;
  proposed_by_actor_role: string | null;
  derived_from_experience_id: string | null;
  created_at: string;
  evidence_count: number;
}

export interface GovernanceReviewResponseDTO {
  generated_at: string;
  candidates_count: number;
  candidates: CandidateReviewDTO[];
}

export interface AuthResponseDTO {
  token: string;
  actor_id: string;
  actor_role: string;
  trust_zone: string;
  project_scope: string | null;
  expires_at: string;
}

export interface SessionInfoDTO {
  authenticated: boolean;
  actor_id: string;
  actor_role: string;
  trust_zone: string;
  project_scope: string | null;
  expires_at: string;
}
