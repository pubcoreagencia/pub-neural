import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OverviewView } from "./OverviewView";
import { NeuralAPI } from "../api/client";

vi.mock("../api/client", () => ({
  NeuralAPI: {
    getOverview: vi.fn(),
    getGovernanceReview: vi.fn(),
  },
}));

describe("OverviewView Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(NeuralAPI.getGovernanceReview).mockResolvedValue({
      generated_at: "2026-09-16T12:00:00Z",
      candidates_count: 0,
      candidates: [],
    });
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
          project_state: "UNKNOWN",
          blocked_nodes_count: 0,
          latest_signal: null,
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
          project_state: "UNKNOWN",
          blocked_nodes_count: 0,
          latest_signal: null,
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

  it("renders V0.2-A contract: project_state, blocked_nodes, latest_signal, and no synthetic progress", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T05:00:00Z",
      window_days: 14,
      database_health: "HEALTHY",
      projector_health: "HEALTHY",
      projects: [
        {
          project_id: "pub-ecom",
          observed_repository_count: 1,
          observation_count: 50,
          activity_today: 3,
          activity_7d: 15,
          last_observation_at: "2026-09-16T04:30:00Z",
          active_node_count: 12,
          project_state: "UNKNOWN",
          blocked_nodes_count: 0,
          latest_signal: {
            type: "REPOSITORY_OBSERVED",
            timestamp: "2026-09-16T04:30:00Z",
            summary: "Observed commit a1b2c3d on branch main",
            source: "neural_repository_observations",
            locator: "pub-holding/pub-ecom@a1b2c3d",
          },
        },
        {
          project_id: "pub-core",
          observed_repository_count: 0,
          observation_count: 0,
          activity_today: 0,
          activity_7d: 0,
          last_observation_at: null,
          active_node_count: 8,
          project_state: "UNKNOWN",
          blocked_nodes_count: 2,
          latest_signal: {
            type: "TASK_EXPERIENCE_RECORDED",
            timestamp: "2026-09-16T04:15:00Z",
            summary: "Task task-102 completed with status SUCCESS: Upgrade auth module",
            source: "neural_events",
            locator: "evt-uuid-456",
          },
        },
        {
          project_id: "pub-empty",
          observed_repository_count: 0,
          observation_count: 0,
          activity_today: 0,
          activity_7d: 0,
          last_observation_at: null,
          active_node_count: 0,
          project_state: "UNKNOWN",
          blocked_nodes_count: 0,
          latest_signal: null,
        },
      ],
      daily_activity: [],
    });

    render(<OverviewView />);

    await waitFor(() => {
      // 1. Project States (strictly UNKNOWN)
      expect(screen.getAllByText("UNKNOWN").length).toBeGreaterThanOrEqual(3);

      // 2. Blocked Nodes
      expect(screen.getByText("Blocked Nodes: 2")).toBeDefined();
      expect(screen.getAllByText("Blocked Nodes: 0").length).toBeGreaterThanOrEqual(2);

      // 3. Operational Signals
      expect(screen.getByText("TELEMETRY")).toBeDefined();
      expect(screen.getByText("Observed commit a1b2c3d on branch main")).toBeDefined();
      expect(screen.getByText("pub-holding/pub-ecom@a1b2c3d")).toBeDefined();

      expect(screen.getByText("TASK SIGNAL")).toBeDefined();
      expect(screen.getByText("Task task-102 completed with status SUCCESS: Upgrade auth module")).toBeDefined();
      expect(screen.getByText("evt-uuid-456")).toBeDefined();

      expect(screen.getByText("No operational signal recorded")).toBeDefined();

      // 4. Invariants: NO synthetic progress or project health
      expect(screen.queryByText(/Project Progress/i)).toBeNull();
      expect(screen.queryByText(/Progress:/i)).toBeNull();
      expect(screen.queryByText(/Project Health:/i)).toBeNull();
    });
  });

  it("renders candidate knowledge awaiting governance review", async () => {
    vi.mocked(NeuralAPI.getOverview).mockResolvedValueOnce({
      generated_at: "2026-09-16T04:00:00Z",
      window_days: 7,
      database_health: "HEALTHY",
      projector_health: "HEALTHY",
      projects: [],
      daily_activity: [],
    });

    vi.mocked(NeuralAPI.getGovernanceReview).mockResolvedValueOnce({
      generated_at: "2026-09-16T12:00:00Z",
      candidates_count: 1,
      candidates: [
        {
          id: "finding:pub-neural:task-test:1",
          entity_type: "LESSON",
          title: "Supabase pgcrypto search_path configuration",
          summary: "Must include extensions in search path",
          content: "Detailed content",
          promotion_state: "CANDIDATE",
          promotion_reason: "Discovered during task-test",
          conflict_state: "RESOLVED",
          scope: "PROJECT",
          project_id: "pub-neural",
          trust_zone: "tz_internal_holding",
          originating_event_id: "evt-001",
          originating_event_type: "TASK_EXPERIENCE_RECORDED",
          proposed_by_actor_id: "autonomous-gate",
          proposed_by_actor_role: "AGENT",
          derived_from_experience_id: "experience:pub-neural:task-test",
          created_at: "2026-09-16T12:00:00Z",
          evidence_count: 1,
        },
      ],
    });

    render(<OverviewView />);

    await waitFor(() => {
      expect(screen.getByText(/Candidate Knowledge Awaiting Governance \(1\)/i)).toBeDefined();
      expect(screen.getByText("Supabase pgcrypto search_path configuration")).toBeDefined();
      expect(screen.getByText("LESSON • CANDIDATE")).toBeDefined();
      expect(screen.getByText(/Proposed By: autonomous-gate \(AGENT\)/i)).toBeDefined();
    });
  });
});
