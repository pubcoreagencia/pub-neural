import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { EventInspector } from "./EventInspector";
import { NeuralAPI } from "../api/client";
import type { EventDetailDTO } from "../api/types";

describe("EventInspector Component", () => {
  it("renders placeholder when no eventId provided", () => {
    render(<EventInspector eventId={null} />);
    expect(screen.getByText(/Select an event in the timeline to inspect audit payload/i)).toBeDefined();
  });

  it("loads and displays deep event details with temporal label and actor governance", async () => {
    const mockEvent: EventDetailDTO = {
      id: "0191e4f0-0020-7000-8000-000000000002",
      global_sequence: 42,
      event_type: "DECISION_PROMOTED",
      event_version: 1,
      payload_schema_version: 1,
      producer_version: "v0.3.0",
      stream_id: "stream:decision:pub-ecom:auth",
      stream_version: 2,
      actor_id: "actor:agent:test-worker",
      actor_role: "SYSTEM_AGENT",
      payload: {
        node_id: "decision:pub-ecom:auth-strategy",
        decision: "Adopt SSR cookie session tokens",
        confidence: 0.98,
        machine_secret: "[REDACTED]",
      },
      signature: "sig_abc1234567890",
      recorded_at: "2026-03-01T14:30:00Z",
      parent_event_ids: ["0191e4f0-0010-7000-8000-000000000001"],
    };

    vi.spyOn(NeuralAPI, "getEventDetail").mockResolvedValueOnce(mockEvent);

    const onNavigateEntity = vi.fn();
    const onSelectEvent = vi.fn();

    render(
      <EventInspector
        eventId="0191e4f0-0020-7000-8000-000000000002"
        onNavigateEntity={onNavigateEntity}
        onSelectEvent={onSelectEvent}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Seq #42 • DECISION_PROMOTED/i)).toBeDefined();
    });

    // Check temporal label
    expect(screen.getByText("EVENT TIME (IMMUTABLE LEDGER RECORD)")).toBeDefined();
    expect(screen.getByText("2026-03-01T14:30:00Z")).toBeDefined();

    // Check actor & stream governance
    expect(screen.getByText("actor:agent:test-worker")).toBeDefined();
    expect(screen.getByText("SYSTEM_AGENT")).toBeDefined();
    expect(screen.getByText("stream:decision:pub-ecom:auth")).toBeDefined();

    // Check causal parents
    expect(screen.getByText("0191e4f0-0010-7000-8000-000000000001")).toBeDefined();

    // Check associated entity affordance
    const focusBtn = screen.getByText("Focus in Graph →");
    expect(focusBtn).toBeDefined();
    fireEvent.click(focusBtn);
    expect(onNavigateEntity).toHaveBeenCalledWith("decision:pub-ecom:auth-strategy");

    // Check sanitized payload display
    expect(screen.getByText(/Adopt SSR cookie session tokens/)).toBeDefined();
    expect(screen.getByText(/\[REDACTED\]/)).toBeDefined();
  });

  it("handles event loading error", async () => {
    vi.spyOn(NeuralAPI, "getEventDetail").mockRejectedValueOnce(new Error("Event 404 Not Found"));

    render(<EventInspector eventId="non-existent" />);

    await waitFor(() => {
      expect(screen.getByText("Event 404 Not Found")).toBeDefined();
    });
  });
});
