import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { SystemStatusBar } from "./SystemStatusBar";
import { NeuralAPI } from "../api/client";
import type { SystemStatusDTO } from "../api/types";

describe("SystemStatusBar Component", () => {
  const mockHealthyStatus: SystemStatusDTO = {
    status: "HEALTHY",
    database_connected: true,
    postgresql_version: "PostgreSQL 16.8 (Debian 16.8-1.pgdg120+1)",
    active_trust_zone: "tz_internal_holding",
    active_actor_role: "SYSTEM_AGENT",
    projector_checkpoints: [
      {
        projector_name: "entity_projector",
        last_processed_global_sequence: 150,
        status: "ACTIVE",
        last_checkpoint_at: "2026-03-01T15:00:00Z",
        error_detail: null,
      },
    ],
    capabilities: {
      database_engine: "ACTIVE (PostgreSQL 16 + pgvector HNSW)",
      event_sourcing: "ACTIVE (Append-only canonical ledger)",
      rls_governance: "ACTIVE (Row Level Security enforced)",
    },
    server_time: "2026-03-01T15:00:05Z",
  };

  it("renders HEALTHY status badge with PostgreSQL version and governance details", async () => {
    vi.spyOn(NeuralAPI, "getStatus").mockResolvedValueOnce(mockHealthyStatus);

    const onViewModeChange = vi.fn();

    render(
      <SystemStatusBar
        viewMode="graph"
        onViewModeChange={onViewModeChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("HEALTHY")).toBeDefined();
    });

    expect(screen.getByText("PostgreSQL 16.8")).toBeDefined();
    expect(screen.getByText("tz_internal_holding")).toBeDefined();
    expect(screen.getByText("SYSTEM_AGENT")).toBeDefined();
    expect(screen.getByText("1")).toBeDefined(); // Checkpoints count
  });

  it("toggles view mode between Knowledge Graph and Event Timeline", async () => {
    vi.spyOn(NeuralAPI, "getStatus").mockResolvedValueOnce(mockHealthyStatus);

    const onViewModeChange = vi.fn();

    render(
      <SystemStatusBar
        viewMode="graph"
        onViewModeChange={onViewModeChange}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("HEALTHY")).toBeDefined();
    });

    const timelineBtn = screen.getByText("◷ Event Timeline");
    fireEvent.click(timelineBtn);
    expect(onViewModeChange).toHaveBeenCalledWith("timeline");

    const graphBtn = screen.getByText("✦ Knowledge Graph");
    fireEvent.click(graphBtn);
    expect(onViewModeChange).toHaveBeenCalledWith("graph");
  });

  it("renders UNAVAILABLE status badge when database_connected is false", async () => {
    vi.spyOn(NeuralAPI, "getStatus").mockResolvedValueOnce({
      ...mockHealthyStatus,
      status: "UNAVAILABLE",
      database_connected: false,
    });

    render(
      <SystemStatusBar
        viewMode="graph"
        onViewModeChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("UNAVAILABLE")).toBeDefined();
    });
  });

  it("renders ERROR status badge when status API call fails", async () => {
    vi.spyOn(NeuralAPI, "getStatus").mockRejectedValueOnce(new Error("500 Internal Server Error"));

    render(
      <SystemStatusBar
        viewMode="graph"
        onViewModeChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("ERROR")).toBeDefined();
    });
  });

  it("shows capabilities popover when clicked", async () => {
    vi.spyOn(NeuralAPI, "getStatus").mockResolvedValueOnce(mockHealthyStatus);

    render(
      <SystemStatusBar
        viewMode="graph"
        onViewModeChange={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Capabilities ▾")).toBeDefined();
    });

    fireEvent.click(screen.getByText("Capabilities ▾"));
    expect(screen.getByText("VERIFIED CAPABILITIES")).toBeDefined();
    expect(screen.getByText("database_engine")).toBeDefined();
  });
});
