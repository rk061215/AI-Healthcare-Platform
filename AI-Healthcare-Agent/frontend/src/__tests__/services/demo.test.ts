import { describe, it, expect, vi, beforeEach } from "vitest";
import type { Mock } from "vitest";

vi.mock("@/services/api-client", () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import { apiClient } from "@/services/api-client";
import { demoService } from "@/services/demo";

describe("demoService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("upload should POST multipart to /demo/upload", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: { id: "1" } });
    const file = new File(["test"], "report.pdf", { type: "application/pdf" });
    await demoService.upload(file);
    expect(apiClient.post).toHaveBeenCalledWith(
      "/demo/upload",
      expect.any(FormData),
    );
  });

  it("ask should POST form-urlencoded to /demo/ask", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: { reply: "ok" } });
    await demoService.ask({ question: "What is this?", report_id: "r1" });
    expect(apiClient.post).toHaveBeenCalledWith(
      "/demo/ask",
      expect.any(URLSearchParams),
      { headers: { "Content-Type": "application/x-www-form-urlencoded" } },
    );
  });

  it("getScenarios should GET /demo/scenarios", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: [] });
    await demoService.getScenarios();
    expect(apiClient.get).toHaveBeenCalledWith("/demo/scenarios");
  });

  it("reset should POST /demo/reset", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({});
    await demoService.reset();
    expect(apiClient.post).toHaveBeenCalledWith("/demo/reset");
  });
});
