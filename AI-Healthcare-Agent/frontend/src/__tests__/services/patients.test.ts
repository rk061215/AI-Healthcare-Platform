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
import { patientService } from "@/services/patients";
import type { PatientProfile } from "@/types";

const mockProfile: PatientProfile = {
  id: "1",
  email: "patient@example.com",
  full_name: "Patient User",
  phone: "1234567890",
  date_of_birth: "1990-01-01",
  gender: "male",
  blood_group: "O+",
  address: "123 Main St",
  emergency_contact: "Jane Doe",
  emergency_phone: "0987654321",
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
};

describe("patientService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getProfile should GET /patients/me", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: mockProfile });
    const result = await patientService.getProfile();
    expect(apiClient.get).toHaveBeenCalledWith("/patients/me");
    expect(result).toEqual(mockProfile);
  });

  it("updateProfile should PATCH /patients/me", async () => {
    const updates: Partial<PatientProfile> = { full_name: "Updated Name" };
    (apiClient.patch as Mock).mockResolvedValueOnce({ data: { ...mockProfile, ...updates } });
    const result = await patientService.updateProfile(updates);
    expect(apiClient.patch).toHaveBeenCalledWith("/patients/me", updates);
    expect(result.full_name).toBe("Updated Name");
  });

  it("getMyDoctors should GET /patients/me/doctors", async () => {
    const mockDoctors = [
      { id: "d1", full_name: "Dr. Smith", specialization: "Cardiology" },
    ];
    (apiClient.get as Mock).mockResolvedValueOnce({ data: mockDoctors });
    const result = await patientService.getMyDoctors();
    expect(apiClient.get).toHaveBeenCalledWith("/patients/me/doctors");
    expect(result).toEqual(mockDoctors);
  });
});
