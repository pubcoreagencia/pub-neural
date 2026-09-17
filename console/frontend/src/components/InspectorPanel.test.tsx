import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { InspectorPanel } from "./InspectorPanel";
import { NeuralAPI } from "../api/client";
import type { EntityDetailDTO } from "../api/types";

describe("InspectorPanel Component", () => {
  it("renders empty state placeholder when no entity selected", () => {
    render(<InspectorPanel entityId={null} />);
    expect(screen.getByText(/Select an entity node in the canvas/i)).toBeDefined();
  });

  it("renders full deep inspector details when entity loads", async () => {
    const mockDetail: EntityDetailDTO = {
      id: "decision:pub-ecom:auth-strategy",
      entity_type: "DECISION",
      title: "Supabase SSR Session Tokens",
      slug: "auth-strategy",
      summary: "Auth session token refresh architecture",
      content: "Detailed markdown content about authentication tokens.",
      promotion_state: "CANDIDATE",
      promotion_reason: "Passed preliminary gate",
      conflict_state: "NONE",
      confidence_score: 0.98,
      superseded_by: null,
      valid_from: "2026-01-01T00:00:00Z",
      valid_until: null,
      recorded_from: "2026-01-01T12:00:00Z",
      recorded_until: null,
      is_active: true,
      originating_event_id: "0191e4f0-0020-7000-8000-000000000002",
      last_transition_event_id: null,
      project_id: "pub-ecom",
      trust_zone: "tz_internal_holding",
      created_at: "2026-01-01T12:00:00Z",
      updated_at: "2026-01-01T12:00:00Z",
      evidence: [
        {
          id: "ev-1",
          source_id: "src-1",
          repository: "pubcore/pub-ecom",
          commit_sha: "abc123456789",
          file_path: "docs/auth.md",
          start_line: 10,
          end_line: 25,
          exact_quote: "Tokens devem ser atualizados no middleware.",
          confidence: 0.99,
        },
      ],
      incoming_relations_count: 2,
      outgoing_relations_count: 1,
    };

    vi.spyOn(NeuralAPI, "getEntityDetail").mockResolvedValueOnce(mockDetail);

    render(<InspectorPanel entityId="decision:pub-ecom:auth-strategy" />);

    await waitFor(() => {
      expect(screen.getByText("Supabase SSR Session Tokens")).toBeDefined();
    });

    // Check Identity & Type
    expect(screen.getByText("DECISION")).toBeDefined();
    expect(screen.getByText("decision:pub-ecom:auth-strategy")).toBeDefined();

    // Check State
    expect(screen.getByText("CANDIDATE")).toBeDefined();
    expect(screen.getByText("98%")).toBeDefined();

    // Check Bi-temporal
    expect(screen.getByText("BUSINESS TIME (VALIDITY)")).toBeDefined();
    expect(screen.getByText("SYSTEM TIME (AUDIT RECORD)")).toBeDefined();

    // Check Evidence
    expect(screen.getByText(/"Tokens devem ser atualizados no middleware."/i)).toBeDefined();
    expect(screen.getByText(/docs\/auth.md/)).toBeDefined();

    // Check Relations
    expect(screen.getByText("Incoming Relations")).toBeDefined();
    expect(screen.getByText("Outgoing Relations")).toBeDefined();
  });

  it("switches tabs between entity inspector and event inspector when both are active", async () => {
    const mockDetail: EntityDetailDTO = {
      id: "decision:pub-ecom:auth-strategy",
      entity_type: "DECISION",
      title: "Supabase SSR Session Tokens",
      slug: "auth-strategy",
      summary: "Auth session token refresh architecture",
      content: "Detailed markdown content about authentication tokens.",
      promotion_state: "CANDIDATE",
      promotion_reason: null,
      conflict_state: "NONE",
      confidence_score: 0.95,
      superseded_by: null,
      valid_from: "2026-01-01T00:00:00Z",
      valid_until: null,
      recorded_from: "2026-01-01T12:00:00Z",
      recorded_until: null,
      is_active: true,
      originating_event_id: "0191e4f0-0020-7000-8000-000000000002",
      last_transition_event_id: null,
      project_id: "pub-ecom",
      trust_zone: "tz_internal_holding",
      created_at: "2026-01-01T12:00:00Z",
      updated_at: "2026-01-01T12:00:00Z",
      evidence: [],
      incoming_relations_count: 0,
      outgoing_relations_count: 0,
    };

    const mockEvent = {
      id: "0191e4f0-0020-7000-8000-000000000002",
      global_sequence: 15,
      event_type: "DECISION_PROMOTED",
      event_version: 1,
      payload_schema_version: 1,
      producer_version: "v0.3.0",
      stream_id: "stream:test",
      stream_version: 1,
      actor_id: "actor:test",
      actor_role: "SYSTEM_AGENT",
      payload: { note: "test" },
      signature: null,
      recorded_at: "2026-01-01T12:00:00Z",
      parent_event_ids: [],
    };

    vi.spyOn(NeuralAPI, "getEntityDetail").mockResolvedValue(mockDetail);
    vi.spyOn(NeuralAPI, "getEventDetail").mockResolvedValue(mockEvent);

    const onSelectEvent = vi.fn();

    const { rerender } = render(
      <InspectorPanel
        entityId="decision:pub-ecom:auth-strategy"
        eventId="0191e4f0-0020-7000-8000-000000000002"
        activeTab="entity"
        onSelectEvent={onSelectEvent}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Supabase SSR Session Tokens")).toBeDefined();
    });

    // Check tab header exists
    expect(screen.getByText("✦ Entity Inspector")).toBeDefined();
    expect(screen.getByText("◷ Event Inspector")).toBeDefined();

    // Rerender with activeTab="event"
    rerender(
      <InspectorPanel
        entityId="decision:pub-ecom:auth-strategy"
        eventId="0191e4f0-0020-7000-8000-000000000002"
        activeTab="event"
        onSelectEvent={onSelectEvent}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Seq #15 • DECISION_PROMOTED/)).toBeDefined();
    });
  });
});

