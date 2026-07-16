import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "@/lib/store/auth-store";
import type { User } from "@/types";

const mockUser: User = {
  id: "1",
  email: "test@example.com",
  full_name: "Test User",
  role: "patient",
  phone: "1234567890",
};

describe("useAuthStore", () => {
  beforeEach(() => {
    useAuthStore.setState({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      rememberMe: false,
      isLoading: false,
    });
  });

  it("should have initial state with null user/token/refreshToken", () => {
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
    expect(state.rememberMe).toBe(false);
  });

  it("setAuth should set user, token, refreshToken", () => {
    useAuthStore.getState().setAuth(mockUser, "access-token", "refresh-token", true);
    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.token).toBe("access-token");
    expect(state.refreshToken).toBe("refresh-token");
    expect(state.isAuthenticated).toBe(true);
    expect(state.rememberMe).toBe(true);
  });

  it("setTokens should update tokens", () => {
    useAuthStore.getState().setTokens("new-access", "new-refresh");
    const state = useAuthStore.getState();
    expect(state.token).toBe("new-access");
    expect(state.refreshToken).toBe("new-refresh");
  });

  it("logout should clear all auth state", () => {
    useAuthStore.getState().setAuth(mockUser, "token", "refresh");
    useAuthStore.getState().logout();
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.refreshToken).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
  });

  it("updateUser should merge user updates", () => {
    useAuthStore.getState().setAuth(mockUser, "token", "refresh");
    useAuthStore.getState().updateUser({ full_name: "Updated Name" });
    const state = useAuthStore.getState();
    expect(state.user?.full_name).toBe("Updated Name");
    expect(state.user?.email).toBe("test@example.com");
  });

  it("getRole should return user role", () => {
    useAuthStore.getState().setAuth(mockUser, "token", "refresh");
    expect(useAuthStore.getState().getRole()).toBe("patient");
  });

  it("getRole should return null when no user", () => {
    const role = useAuthStore.getState().getRole();
    expect(role).toBeNull();
  });

  it("setLoading should update loading state", () => {
    useAuthStore.getState().setLoading(true);
    expect(useAuthStore.getState().isLoading).toBe(true);
    useAuthStore.getState().setLoading(false);
    expect(useAuthStore.getState().isLoading).toBe(false);
  });

  it("setRememberMe should update rememberMe flag", () => {
    useAuthStore.getState().setRememberMe(true);
    expect(useAuthStore.getState().rememberMe).toBe(true);
    useAuthStore.getState().setRememberMe(false);
    expect(useAuthStore.getState().rememberMe).toBe(false);
  });
});
