import type {
  GraphResponseDTO,
  EntityDetailDTO,
  SearchResponseDTO,
  SystemStatusDTO,
  EventListResponseDTO,
  EventDetailDTO,
  GovernanceReviewResponseDTO,
  OverviewResponseDTO,
  AuthResponseDTO,
  SessionInfoDTO,
  ProjectRegistryListDTO,
  ProjectRegistryItemDTO,
  HoldingProjectListDTO,
  HoldingProjectItemDTO,
  ProjectRepositoryAssociationDTO,
  GovernanceOntologyQueuesDTO,
  ActivityListResponseDTO,
} from "./types";

const SESSION_STORAGE_KEY = "pub_neural_session_token";

let inMemoryToken: string | null = null;

export function getApiBaseUrl(): string {
  const envUrl = import.meta.env.VITE_API_BASE_URL;
  if (envUrl && typeof envUrl === "string" && envUrl.trim().length > 0) {
    const trimmed = envUrl.trim().replace(/\/+$/, "");
    return trimmed.endsWith("/api/v1") ? trimmed : `${trimmed}/api/v1`;
  }
  // In development mode (vite dev), default to local backend server.
  // In production builds without explicit VITE_API_BASE_URL, default to relative '/api/v1'.
  if (import.meta.env.DEV) {
    return "http://127.0.0.1:8080/api/v1";
  }
  return "/api/v1";
}

export function getBearerToken(): string | undefined {
  if (inMemoryToken) {
    return inMemoryToken;
  }
  try {
    if (typeof window !== "undefined" && window.sessionStorage) {
      const stored = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
      if (stored) {
        inMemoryToken = stored;
        return stored;
      }
    }
  } catch {
    // Ignore storage errors in restrictive environments
  }
  return import.meta.env.VITE_NEURAL_BEARER_TOKEN;
}

export function setSessionToken(token: string | null): void {
  inMemoryToken = token;
  try {
    if (typeof window !== "undefined" && window.sessionStorage) {
      if (token) {
        window.sessionStorage.setItem(SESSION_STORAGE_KEY, token);
      } else {
        window.sessionStorage.removeItem(SESSION_STORAGE_KEY);
      }
    }
  } catch {
    // Ignore storage errors
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: { method?: string; body?: any; headers?: Record<string, string> } = {}
): Promise<T> {
  const apiBase = getApiBaseUrl();
  const token = getBearerToken();
  const headers: Record<string, string> = {
    ...options.headers,
  };
  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${apiBase}${endpoint}`, {
    method: options.method || "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    let errorDetail = response.statusText;
    try {
      const errJson = await response.json();
      if (errJson && errJson.detail) {
        errorDetail = errJson.detail;
      }
    } catch {
      // Use statusText if body is not JSON
    }
    const err = new Error(`API error: ${response.status} ${errorDetail}`);
    (err as any).status = response.status;
    throw err;
  }
  return response.json();
}

export const NeuralAPI = {
  async login(credentials: {
    actorId: string;
    secret: string;
    trustZone?: string;
    projectScope?: string;
  }): Promise<AuthResponseDTO> {
    const res = await fetchApi<AuthResponseDTO>("/auth/login", {
      method: "POST",
      body: {
        actor_id: credentials.actorId,
        secret: credentials.secret,
        trust_zone: credentials.trustZone || "tz_internal_holding",
        project_scope: credentials.projectScope || null,
      },
    });
    setSessionToken(res.token);
    return res;
  },

  async logout(): Promise<void> {
    try {
      await fetchApi<{ revoked: boolean }>("/auth/logout", {
        method: "POST",
      });
    } finally {
      setSessionToken(null);
    }
  },

  async getSession(): Promise<SessionInfoDTO> {
    return fetchApi<SessionInfoDTO>("/auth/session");
  },

  async getStatus(): Promise<SystemStatusDTO> {
    return fetchApi<SystemStatusDTO>("/status");
  },

  async getOverview(windowDays: number = 14): Promise<OverviewResponseDTO> {
    return fetchApi<OverviewResponseDTO>(`/overview?window_days=${windowDays}`);
  },

  async search(query: string): Promise<SearchResponseDTO> {
    return fetchApi<SearchResponseDTO>(`/search?q=${encodeURIComponent(query)}`);
  },

  async getNeighborhood(
    entityId: string,
    depth: number = 2
  ): Promise<GraphResponseDTO> {
    return fetchApi<GraphResponseDTO>(`/entities/${entityId}/neighborhood?depth=${depth}`);
  },

  async getEntityDetail(entityId: string): Promise<EntityDetailDTO> {
    return fetchApi<EntityDetailDTO>(`/entities/${entityId}`);
  },

  async getEvents(params?: {
    limit?: number;
    offset?: number;
    streamId?: string;
    eventType?: string;
  }): Promise<EventListResponseDTO> {
    const searchParams = new URLSearchParams();
    if (params?.limit !== undefined) searchParams.set("limit", String(params.limit));
    if (params?.offset !== undefined) searchParams.set("offset", String(params.offset));
    if (params?.streamId) searchParams.set("stream_id", params.streamId);
    if (params?.eventType) searchParams.set("event_type", params.eventType);
    const qs = searchParams.toString();
    return fetchApi<EventListResponseDTO>(`/events${qs ? `?${qs}` : ""}`);
  },

  async getEventDetail(eventId: string): Promise<EventDetailDTO> {
    return fetchApi<EventDetailDTO>(`/events/${encodeURIComponent(eventId)}`);
  },

  async getGovernanceReview(): Promise<GovernanceReviewResponseDTO> {
    return fetchApi<GovernanceReviewResponseDTO>("/governance/review");
  },

  async getGovernanceOntologyQueues(): Promise<GovernanceOntologyQueuesDTO> {
    return fetchApi<GovernanceOntologyQueuesDTO>("/governance/ontology");
  },

  async getHoldingProjects(params?: {
    projectType?: string;
    lifecycleStatus?: string;
    isActive?: boolean;
    ontologyStatus?: string;
  }): Promise<HoldingProjectListDTO> {
    const searchParams = new URLSearchParams();
    if (params?.projectType) searchParams.set("project_type", params.projectType);
    if (params?.lifecycleStatus) searchParams.set("lifecycle_status", params.lifecycleStatus);
    if (params?.isActive !== undefined) searchParams.set("is_active", String(params.isActive));
    if (params?.ontologyStatus) searchParams.set("ontology_status", params.ontologyStatus);
    const qs = searchParams.toString();
    return fetchApi<HoldingProjectListDTO>(`/projects${qs ? `?${qs}` : ""}`);
  },

  async getHoldingProjectDetail(projectId: string): Promise<HoldingProjectItemDTO> {
    return fetchApi<HoldingProjectItemDTO>(`/projects/${encodeURIComponent(projectId)}`);
  },

  async getProjectRepositories(projectId: string): Promise<ProjectRepositoryAssociationDTO[]> {
    return fetchApi<ProjectRepositoryAssociationDTO[]>(`/projects/${encodeURIComponent(projectId)}/repositories`);
  },

  async getRepositories(): Promise<any[]> {
    return fetchApi<any[]>("/repositories");
  },

  async getUnclassifiedRepositories(): Promise<ProjectRegistryItemDTO[]> {
    return fetchApi<ProjectRegistryItemDTO[]>("/repositories/unclassified");
  },

  async getProjects(params?: {
    category?: string;
    isActive?: boolean;
    isArchived?: boolean;
  }): Promise<ProjectRegistryListDTO> {
    const searchParams = new URLSearchParams();
    searchParams.set("view", "repositories");
    if (params?.category) searchParams.set("category", params.category);
    if (params?.isActive !== undefined) searchParams.set("is_active", String(params.isActive));
    if (params?.isArchived !== undefined) searchParams.set("is_archived", String(params.isArchived));
    const qs = searchParams.toString();
    return fetchApi<ProjectRegistryListDTO>(`/projects${qs ? `?${qs}` : ""}`);
  },

  async getProjectDetail(projectId: string): Promise<{
    registry: ProjectRegistryItemDTO;
    observations: {
      observed_repositories: number;
      total_observations: number;
      today_observations: number;
      seven_day_observations: number;
      last_observed_at: string | null;
    };
    knowledge: {
      active_nodes: number;
      candidate_nodes: number;
      adopted_nodes: number;
      blocked_nodes: number;
    };
  }> {
    return fetchApi(`/projects/${encodeURIComponent(projectId)}`);
  },

  async getActivity(params?: {
    windowDays?: number;
    projectId?: string;
    repositoryId?: string;
    activityType?: string;
    limit?: number;
  }): Promise<ActivityListResponseDTO> {
    const searchParams = new URLSearchParams();
    if (params?.windowDays) searchParams.set("window_days", String(params.windowDays));
    if (params?.projectId) searchParams.set("project_id", params.projectId);
    if (params?.repositoryId) searchParams.set("repository_id", params.repositoryId);
    if (params?.activityType) searchParams.set("activity_type", params.activityType);
    if (params?.limit) searchParams.set("limit", String(params.limit));
    const qs = searchParams.toString();
    return fetchApi<ActivityListResponseDTO>(`/activity${qs ? `?${qs}` : ""}`);
  },

  async getProjectActivity(projectId: string, windowDays: number = 14, limit: number = 50): Promise<ActivityListResponseDTO> {
    const searchParams = new URLSearchParams();
    searchParams.set("window_days", String(windowDays));
    searchParams.set("limit", String(limit));
    return fetchApi<ActivityListResponseDTO>(`/projects/${encodeURIComponent(projectId)}/activity?${searchParams.toString()}`);
  },

  async getRepositoryActivity(repositoryId: string, windowDays: number = 14, limit: number = 50): Promise<ActivityListResponseDTO> {
    const searchParams = new URLSearchParams();
    searchParams.set("window_days", String(windowDays));
    searchParams.set("limit", String(limit));
    return fetchApi<ActivityListResponseDTO>(`/repositories/${encodeURIComponent(repositoryId)}/activity?${searchParams.toString()}`);
  },
};
