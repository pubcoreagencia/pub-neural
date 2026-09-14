import type { GraphResponseDTO, EntityDetailDTO, SearchResponseDTO, SystemStatusDTO } from "./types";

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
};
