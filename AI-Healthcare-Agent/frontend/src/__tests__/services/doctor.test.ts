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
import { doctorService } from "@/services/doctor";
import type { PatientProfile } from "@/types";

const mockDoctorProfile = {
  id: "d1",
  email: "doctor@example.com",
  full_name: "Dr. Smith",
  specialization: "Cardiology",
};

const mockPatientProfile: PatientProfile = {
  id: "p1",
  email: "patient@example.com",
  full_name: "Patient User",
  phone: null,
  date_of_birth: null,
  gender: null,
  blood_group: null,
  address: null,
  emergency_contact: null,
  emergency_phone: null,
  is_active: true,
  created_at: "2024-01-01T00:00:00Z",
};

describe("doctorService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("getProfile should GET /doctors/me", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: mockDoctorProfile });
    const result = await doctorService.getProfile();
    expect(apiClient.get).toHaveBeenCalledWith("/doctors/me");
    expect(result).toEqual(mockDoctorProfile);
  });

  it("getPatients should GET /doctors/me/patients", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: [mockPatientProfile],
    });
    const result = await doctorService.getPatients();
    expect(apiClient.get).toHaveBeenCalledWith("/doctors/me/patients");
    expect(result).toEqual([mockPatientProfile]);
  });

  it("assignPatient should POST /doctors/me/patients/{id}/assign", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({});
    await doctorService.assignPatient("p1");
    expect(apiClient.post).toHaveBeenCalledWith(
      "/doctors/me/patients/p1/assign",
    );
  });
});
