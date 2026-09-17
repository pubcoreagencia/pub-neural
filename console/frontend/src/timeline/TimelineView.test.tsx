import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { TimelineView } from "./TimelineView";
import { NeuralAPI } from "../api/client";
import type { EventListResponseDTO } from "../api/types";

describe("TimelineView Component", () => {
  const mockEventsResponse: EventListResponseDTO = {
    events: [
      {
        id: "0191e4f0-0020-7000-8000-000000000002",
        global_sequence: 105,
        event_type: "DECISION_PROMOTED",
        event_version: 1,
        producer_version: "v0.3.0",
        stream_id: "entity:decision:pub-ecom:auth",
        stream_version: 2,
        actor_id: "actor:agent:test-worker",
        actor_role: "SYSTEM_AGENT",
        recorded_at: "2026-03-01T15:00:00Z",
      },
      {
        id: "0191e4f0-0010-7000-8000-000000000001",
        global_sequence: 104,
        event_type: "ENTITY_CREATED",
        event_version: 1,
        producer_version: "v0.3.0",
        stream_id: "stream:system:bootstrap",
        stream_version: 1,
        actor_id: "actor:human:matheus",
        actor_role: "ADMIN",
        recorded_at: "2026-03-01T14:00:00Z",
      },
    ],
    total_returned: 2,
    limit: 50,
    offset: 0,
  };

  it("renders chronological events list with metadata and timestamps", async () => {
    vi.spyOn(NeuralAPI, "getEvents").mockResolvedValueOnce(mockEventsResponse);

    const onSelectEvent = vi.fn();
    const onNavigateEntity = vi.fn();

    render(
      <TimelineView
        selectedEventId={null}
        onSelectEvent={onSelectEvent}
        onNavigateEntity={onNavigateEntity}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("DECISION_PROMOTED")).toBeDefined();
      expect(screen.getByText("ENTITY_CREATED")).toBeDefined();
    });

    // Check sequence numbers
    expect(screen.getByText("#105")).toBeDefined();
    expect(screen.getByText("#104")).toBeDefined();

    // Check actors
    expect(screen.getByText("(actor:agent:test-worker)")).toBeDefined();
    expect(screen.getByText("(actor:human:matheus)")).toBeDefined();

    // Check Event Time timestamps
    expect(screen.getByText("2026-03-01T15:00:00Z")).toBeDefined();
    expect(screen.getByText("2026-03-01T14:00:00Z")).toBeDefined();

    // Check entity navigation affordance on stream with entity: prefix
    const viewEntityBtn = screen.getByText("View Entity in Graph →");
    expect(viewEntityBtn).toBeDefined();
    fireEvent.click(viewEntityBtn);
    expect(onNavigateEntity).toHaveBeenCalledWith("decision:pub-ecom:auth");
  });

  it("triggers onSelectEvent when clicking an event card", async () => {
    vi.spyOn(NeuralAPI, "getEvents").mockResolvedValueOnce(mockEventsResponse);

    const onSelectEvent = vi.fn();

    render(
      <TimelineView
        selectedEventId={null}
        onSelectEvent={onSelectEvent}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("DECISION_PROMOTED")).toBeDefined();
    });

    fireEvent.click(screen.getByText("DECISION_PROMOTED"));
    expect(onSelectEvent).toHaveBeenCalledWith("0191e4f0-0020-7000-8000-000000000002");
  });

  it("handles filter inputs and queries API with parameters", async () => {
    const getEventsSpy = vi.spyOn(NeuralAPI, "getEvents").mockResolvedValue(mockEventsResponse);

    render(
      <TimelineView
        selectedEventId={null}
        onSelectEvent={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("DECISION_PROMOTED")).toBeDefined();
    });

    const typeInput = screen.getByLabelText("Filter Event Type");
    fireEvent.change(typeInput, { target: { value: "DECISION_PROMOTED" } });

    const applyBtn = screen.getByText("Apply");
    fireEvent.click(applyBtn);

    await waitFor(() => {
      expect(getEventsSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          eventType: "DECISION_PROMOTED",
        })
      );
    });
  });

  it("renders empty state message when no events returned", async () => {
    vi.spyOn(NeuralAPI, "getEvents").mockResolvedValueOnce({
      events: [],
      total_returned: 0,
      limit: 50,
      offset: 0,
    });

    render(
      <TimelineView
        selectedEventId={null}
        onSelectEvent={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("No events found matching current criteria.")).toBeDefined();
    });
  });

  it("renders error alert on fetch failure", async () => {
    vi.spyOn(NeuralAPI, "getEvents").mockRejectedValueOnce(new Error("Database connection dropped"));

    render(
      <TimelineView
        selectedEventId={null}
        onSelectEvent={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Database connection dropped")).toBeDefined();
    });
  });
});
