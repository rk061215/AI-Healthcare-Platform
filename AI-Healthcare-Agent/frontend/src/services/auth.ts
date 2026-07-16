import { apiClient } from "./api-client";
import type {
  AuthResponse,
  DoctorRegisterRequest,
  LoginRequest,
  PatientRegisterRequest,
  UserProfile,
} from "@/types";

export const authService = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post("/auth/login", data);
    return response.data;
  },

  async registerPatient(data: PatientRegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post("/auth/register/patient", data);
    return response.data;
  },

  async registerDoctor(data: DoctorRegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post("/auth/register/doctor", data);
    return response.data;
  },

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post("/auth/logout", { refresh_token: refreshToken });
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post("/auth/refresh", {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  async getMe(): Promise<UserProfile> {
    const response = await apiClient.get("/auth/me");
    return response.data;
  },
};
