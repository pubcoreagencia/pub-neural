import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OverviewView } from "./OverviewView";
import { NeuralAPI } from "../api/client";

vi.mock("../api/client", () => ({
  NeuralAPI: {
    getOverview: vi.fn(),
  },
}));

describe("OverviewView Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders loading state then operational overview data", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T04:00:00Z",
      window_days: 7,
      database_health: "HEALTHY",
      projector_health: "HEALTHY",
      projects: [
        {
          project_id: "pub-ecom",
          observed_repository_count: 1,
          observation_count: 42,
          activity_today: 5,
          activity_7d: 20,
          last_observation_at: "2026-09-16T03:00:00Z",
          active_node_count: 8,
        },
      ],
      daily_activity: [
        {
          day: "2026-09-16",
          project_id: "pub-ecom",
          observed_count: 5,
        },
      ],
    });

    render(<OverviewView />);

    expect(screen.getByText(/Loading Command Center Overview/i)).toBeDefined();

    await waitFor(() => {
      expect(screen.getAllByText("pub-ecom").length).toBeGreaterThan(0);
      expect(screen.getByText(/Database: HEALTHY/i)).toBeDefined();
      expect(screen.getByText(/Projectors: HEALTHY/i)).toBeDefined();
      expect(screen.getByText("42")).toBeDefined();
    });
  });

  it("renders distinct project without repository observations without failing", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T04:00:00Z",
      window_days: 7,
      database_health: "HEALTHY",
      projector_health: "DEGRADED",
      projects: [
        {
          project_id: "pub-holding",
          observed_repository_count: 0,
          observation_count: 0,
          activity_today: 0,
          activity_7d: 0,
          last_observation_at: null,
          active_node_count: 14,
        },
      ],
      daily_activity: [
        {
          day: "2026-09-16",
          project_id: "pub-holding",
          observed_count: 0,
        },
      ],
    });

    render(<OverviewView />);

    await waitFor(() => {
      expect(screen.getAllByText("pub-holding").length).toBeGreaterThan(0);
      expect(screen.getByText(/No repository observations recorded/i)).toBeDefined();
      expect(screen.getByText("14")).toBeDefined();
      expect(screen.getByText(/Projectors: DEGRADED/i)).toBeDefined();
    });
  });
});
