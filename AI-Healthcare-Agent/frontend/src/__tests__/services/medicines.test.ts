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
import { medicineService } from "@/services/medicines";
import type { Medicine } from "@/types";

const mockMedicine: Medicine = {
  id: "1",
  report_id: "r1",
  patient_id: "p1",
  name: "Aspirin",
  dosage: "100mg",
  frequency: "Once daily",
  duration: "30 days",
  route: "Oral",
  instructions: "Take with food",
  start_date: "2024-01-01",
  end_date: "2024-01-31",
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
};

describe("medicineService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("list should GET /medicines", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: [mockMedicine] });
    const result = await medicineService.list();
    expect(apiClient.get).toHaveBeenCalledWith("/medicines");
    expect(result).toEqual([mockMedicine]);
  });

  it("listActive should GET /medicines/active", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: [mockMedicine] });
    const result = await medicineService.listActive();
    expect(apiClient.get).toHaveBeenCalledWith("/medicines/active");
    expect(result).toEqual([mockMedicine]);
  });

  it("get should GET /medicines/{id}", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: mockMedicine });
    const result = await medicineService.get("1");
    expect(apiClient.get).toHaveBeenCalledWith("/medicines/1");
    expect(result).toEqual(mockMedicine);
  });

  it("update should PATCH /medicines/{id}", async () => {
    (apiClient.patch as Mock).mockResolvedValueOnce({ data: mockMedicine });
    const updates: Partial<Medicine> = { dosage: "200mg" };
    const result = await medicineService.update("1", updates);
    expect(apiClient.patch).toHaveBeenCalledWith("/medicines/1", updates);
    expect(result).toEqual(mockMedicine);
  });
});
