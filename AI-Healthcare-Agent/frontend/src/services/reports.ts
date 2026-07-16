import { apiClient } from "./api-client";
import type { Report } from "@/types";

export const reportService = {
  async upload(file: File): Promise<{ id: string; title: string | null; status: string; uploaded_at: string }> {
    const formData = new FormData();
    formData.append("file", file);
    const response = await apiClient.post("/reports/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  },

  async list(): Promise<Report[]> {
    const response = await apiClient.get("/reports");
    return response.data;
  },

  async get(id: string): Promise<Report> {
    const response = await apiClient.get(`/reports/${id}`);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/reports/${id}`);
  },
};
