import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { getApiBaseUrl, NeuralAPI } from "./client";

describe("NeuralAPI Client Configuration", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("defaults to local fallback http://127.0.0.1:8080/api/v1 in development mode when VITE_API_BASE_URL is undefined", () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    vi.stubEnv("DEV", true);
    expect(getApiBaseUrl()).toBe("http://127.0.0.1:8080/api/v1");
  });

  it("defaults to safe relative /api/v1 in production mode when VITE_API_BASE_URL is undefined", () => {
    vi.stubEnv("VITE_API_BASE_URL", "");
    vi.stubEnv("DEV", false);
    expect(getApiBaseUrl()).toBe("/api/v1");
  });

  it("resolves dynamic VITE_API_BASE_URL when defined without trailing slash", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.pub-neural.pages.dev");
    expect(getApiBaseUrl()).toBe("https://api.pub-neural.pages.dev/api/v1");
  });

  it("handles trailing slashes cleanly", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.pub-neural.pages.dev/");
    expect(getApiBaseUrl()).toBe("https://api.pub-neural.pages.dev/api/v1");
  });

  it("preserves explicit /api/v1 if already specified in VITE_API_BASE_URL", () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.pub-neural.pages.dev/api/v1");
    expect(getApiBaseUrl()).toBe("https://api.pub-neural.pages.dev/api/v1");
  });

  it("proves that getStatus calls the configured VITE_API_BASE_URL", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://api.production.neural");
    vi.stubEnv("VITE_NEURAL_BEARER_TOKEN", "test-token-123");

    const fetchSpy = vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ status: "HEALTHY" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    const res = await NeuralAPI.getStatus();
    expect(res).toEqual({ status: "HEALTHY" });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    expect(fetchSpy).toHaveBeenCalledWith(
      "https://api.production.neural/api/v1/status",
      expect.objectContaining({
        headers: {
          Authorization: "Bearer test-token-123",
        },
      })
    );
  });
});
