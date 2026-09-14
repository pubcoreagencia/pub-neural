import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ExplorerSidebar } from "./ExplorerSidebar";
import { NeuralAPI } from "../api/client";
import type { SearchResponseDTO } from "../api/types";

describe("ExplorerSidebar Component", () => {
  it("renders search form and triggers search on submit", async () => {
    const mockResponse: SearchResponseDTO = {
      query: "Tokens",
      status: "SUCCESS",
      results: [
        {
          target_id: "decision:pub-ecom:auth-strategy",
          target_type: "DECISION",
          title: "Supabase SSR Session Tokens",
          snippet: "Auth session token refresh architecture",
          lexical_rank: 1,
          dense_rank: 1,
          rrf_score: 0.0327,
          trust_zone: "tz_internal_holding",
          project_id: "pub-ecom",
          originating_event_id: "0191e4f0-0020-7000-8000-000000000002",
        },
      ],
      abstention_decision: {
        accepted: true,
        reason: null,
        top_dense_similarity: 0.95,
        top_rrf_score: 0.0327,
        lexical_candidate_count: 1,
        dense_candidate_count: 1,
      },
      lexical_count: 1,
      dense_count: 1,
    };

    const spy = vi.spyOn(NeuralAPI, "search").mockResolvedValueOnce(mockResponse);
    const onSelect = vi.fn();

    render(<ExplorerSidebar onSelectEntity={onSelect} selectedEntityId={null} />);

    const input = screen.getByPlaceholderText(/Hybrid search/i);
    fireEvent.change(input, { target: { value: "Tokens" } });

    const searchBtn = screen.getByRole("button", { name: /search/i });
    fireEvent.click(searchBtn);

    await waitFor(() => {
      expect(spy).toHaveBeenCalledWith("Tokens");
      expect(screen.getByText("Supabase SSR Session Tokens")).toBeDefined();
    });

    // Select result
    fireEvent.click(screen.getByText("Supabase SSR Session Tokens"));
    expect(onSelect).toHaveBeenCalledWith("decision:pub-ecom:auth-strategy");
  });

  it("displays ABSTAINED banner when search is abstained", async () => {
    const mockAbstained: SearchResponseDTO = {
      query: "Uncertain query",
      status: "ABSTAINED",
      results: [],
      abstention_decision: {
        accepted: false,
        reason: "Dense similarity 0.42 below threshold 0.70",
        top_dense_similarity: 0.42,
        top_rrf_score: 0.0,
        lexical_candidate_count: 0,
        dense_candidate_count: 1,
      },
      lexical_count: 0,
      dense_count: 1,
    };

    vi.spyOn(NeuralAPI, "search").mockResolvedValueOnce(mockAbstained);

    render(<ExplorerSidebar onSelectEntity={vi.fn()} selectedEntityId={null} />);

    const input = screen.getByPlaceholderText(/Hybrid search/i);
    fireEvent.change(input, { target: { value: "Uncertain query" } });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));

    await waitFor(() => {
      expect(screen.getByText(/Retrieval Abstained by Governance/i)).toBeDefined();
      expect(screen.getByText(/Dense similarity 0.42 below threshold 0.70/i)).toBeDefined();
    });
  });

  it("displays NO_MATCH banner when search returns empty", async () => {
    const mockNoMatch: SearchResponseDTO = {
      query: "NonExistentThing",
      status: "NO_MATCH",
      results: [],
      abstention_decision: {
        accepted: true,
        reason: null,
        top_dense_similarity: null,
        top_rrf_score: null,
        lexical_candidate_count: 0,
        dense_candidate_count: 0,
      },
      lexical_count: 0,
      dense_count: 0,
    };

    vi.spyOn(NeuralAPI, "search").mockResolvedValueOnce(mockNoMatch);

    render(<ExplorerSidebar onSelectEntity={vi.fn()} selectedEntityId={null} />);

    const input = screen.getByPlaceholderText(/Hybrid search/i);
    fireEvent.change(input, { target: { value: "NonExistentThing" } });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));

    await waitFor(() => {
      expect(screen.getByText(/No matching entities found for "NonExistentThing"/i)).toBeDefined();
    });
  });
});
