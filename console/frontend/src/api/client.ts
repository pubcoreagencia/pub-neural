import type {
  GraphResponseDTO,
  EntityDetailDTO,
  SearchResponseDTO,
  SystemStatusDTO,
  EventListResponseDTO,
  EventDetailDTO,
  GovernanceReviewResponseDTO,
  OverviewResponseDTO,
} from "./types";

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
  return import.meta.env.VITE_NEURAL_BEARER_TOKEN;
}

async function fetchApi<T>(endpoint: string): Promise<T> {
  const apiBase = getApiBaseUrl();
  const token = getBearerToken();
  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${apiBase}${endpoint}`, {
    headers,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

export const NeuralAPI = {
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
};
