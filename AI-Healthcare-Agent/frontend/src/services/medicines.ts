import { apiClient } from "./api-client";
import type { Medicine } from "@/types";

export const medicineService = {
  async list(): Promise<Medicine[]> {
    const response = await apiClient.get("/medicines");
    return response.data;
  },

  async listActive(): Promise<Medicine[]> {
    const response = await apiClient.get("/medicines/active");
    return response.data;
  },

  async get(id: string): Promise<Medicine> {
    const response = await apiClient.get(`/medicines/${id}`);
    return response.data;
  },

  async update(id: string, data: Partial<Medicine>): Promise<Medicine> {
    const response = await apiClient.patch(`/medicines/${id}`, data);
    return response.data;
  },
};
