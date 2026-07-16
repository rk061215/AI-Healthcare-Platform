import { apiClient } from "./api-client";
import type { PatientProfile, EmergencyAlert } from "@/types";

export const doctorService = {
  async getProfile(): Promise<{ id: string; email: string; full_name: string; specialization: string | null }> {
    const response = await apiClient.get("/doctors/me");
    return response.data;
  },

  async getPatients(): Promise<PatientProfile[]> {
    const response = await apiClient.get("/doctors/me/patients");
    return response.data;
  },

  async assignPatient(patientId: string): Promise<void> {
    await apiClient.post(`/doctors/me/patients/${patientId}/assign`);
  },
};
