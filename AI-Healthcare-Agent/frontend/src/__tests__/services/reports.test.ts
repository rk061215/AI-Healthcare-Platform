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
import { reportService } from "@/services/reports";
import type { Report } from "@/types";

const mockReport: Report = {
  id: "1",
  title: "Blood Test",
  file_type: "pdf",
  status: "completed",
  ocr_text: null,
  extracted_data: null,
  uploaded_at: "2024-01-01T00:00:00Z",
  processed_at: "2024-01-01T01:00:00Z",
};

const mockUploadResult = {
  id: "1",
  title: "Blood Test",
  status: "processing",
  uploaded_at: "2024-01-01T00:00:00Z",
};

describe("reportService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("upload should POST multipart form to /reports/upload", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: mockUploadResult });
    const file = new File(["test"], "report.pdf", { type: "application/pdf" });
    const result = await reportService.upload(file);
    expect(apiClient.post).toHaveBeenCalledWith(
      "/reports/upload",
      expect.any(FormData),
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    expect(result).toEqual(mockUploadResult);
  });

  it("list should GET /reports", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: [mockReport] });
    const result = await reportService.list();
    expect(apiClient.get).toHaveBeenCalledWith("/reports");
    expect(result).toEqual([mockReport]);
  });

  it("get should GET /reports/{id}", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: mockReport });
    const result = await reportService.get("1");
    expect(apiClient.get).toHaveBeenCalledWith("/reports/1");
    expect(result).toEqual(mockReport);
  });

  it("delete should DELETE /reports/{id}", async () => {
    (apiClient.delete as Mock).mockResolvedValueOnce({});
    await reportService.delete("1");
    expect(apiClient.delete).toHaveBeenCalledWith("/reports/1");
  });
});
