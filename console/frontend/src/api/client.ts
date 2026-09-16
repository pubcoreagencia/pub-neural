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

const API_BASE = "http://127.0.0.1:8080/api/v1";
const TOKEN = import.meta.env.VITE_NEURAL_BEARER_TOKEN;

async function fetchApi<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      Authorization: `Bearer ${TOKEN}`,
    },
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
