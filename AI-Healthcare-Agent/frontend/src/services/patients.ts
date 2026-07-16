import { apiClient } from "./api-client";
import type { PatientProfile } from "@/types";

export const patientService = {
  async getProfile(): Promise<PatientProfile> {
    const response = await apiClient.get("/patients/me");
    return response.data;
  },

  async updateProfile(data: Partial<PatientProfile>): Promise<PatientProfile> {
    const response = await apiClient.patch("/patients/me", data);
    return response.data;
  },

  async getMyDoctors(): Promise<{ id: string; full_name: string; specialization: string | null }[]> {
    const response = await apiClient.get("/patients/me/doctors");
    return response.data;
  },
};
