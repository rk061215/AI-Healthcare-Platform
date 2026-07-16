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
import { authService } from "@/services/auth";
import type { AuthResponse, UserProfile } from "@/types";

const mockAuthResponse: AuthResponse = {
  access_token: "access-token",
  refresh_token: "refresh-token",
  token_type: "bearer",
  expires_in: 3600,
  user: {
    id: "1",
    email: "test@example.com",
    full_name: "Test User",
    role: "patient",
    phone: null,
  },
};

const mockUserProfile: UserProfile = {
  id: "1",
  email: "test@example.com",
  full_name: "Test User",
  role: "patient",
  phone: null,
  date_of_birth: null,
  gender: null,
  is_active: true,
};

describe("authService", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("login should POST to /auth/login", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: mockAuthResponse });
    const result = await authService.login({
      email: "test@example.com",
      password: "password",
      role: "patient",
    });
    expect(apiClient.post).toHaveBeenCalledWith("/auth/login", {
      email: "test@example.com",
      password: "password",
      role: "patient",
    });
    expect(result).toEqual(mockAuthResponse);
  });

  it("registerPatient should POST to /auth/register/patient", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: mockAuthResponse });
    const result = await authService.registerPatient({
      email: "patient@example.com",
      password: "password",
      confirm_password: "password",
      full_name: "Patient",
      terms_accepted: true,
    });
    expect(apiClient.post).toHaveBeenCalledWith("/auth/register/patient", {
      email: "patient@example.com",
      password: "password",
      confirm_password: "password",
      full_name: "Patient",
      terms_accepted: true,
    });
    expect(result).toEqual(mockAuthResponse);
  });

  it("registerDoctor should POST to /auth/register/doctor", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: mockAuthResponse });
    const result = await authService.registerDoctor({
      email: "doctor@example.com",
      password: "password",
      confirm_password: "password",
      full_name: "Doctor",
    });
    expect(apiClient.post).toHaveBeenCalledWith("/auth/register/doctor", {
      email: "doctor@example.com",
      password: "password",
      confirm_password: "password",
      full_name: "Doctor",
    });
    expect(result).toEqual(mockAuthResponse);
  });

  it("logout should POST to /auth/logout", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({});
    await authService.logout("refresh-token");
    expect(apiClient.post).toHaveBeenCalledWith("/auth/logout", {
      refresh_token: "refresh-token",
    });
  });

  it("refreshToken should POST to /auth/refresh", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({ data: mockAuthResponse });
    const result = await authService.refreshToken("refresh-token");
    expect(apiClient.post).toHaveBeenCalledWith("/auth/refresh", {
      refresh_token: "refresh-token",
    });
    expect(result).toEqual(mockAuthResponse);
  });

  it("getMe should GET /auth/me", async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: mockUserProfile });
    const result = await authService.getMe();
    expect(apiClient.get).toHaveBeenCalledWith("/auth/me");
    expect(result).toEqual(mockUserProfile);
  });
});
