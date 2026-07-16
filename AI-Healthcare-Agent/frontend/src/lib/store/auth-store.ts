import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  rememberMe: boolean;
  isLoading: boolean;
  setAuth: (user: User, token: string, refreshToken: string, rememberMe?: boolean) => void;
  setLoading: (loading: boolean) => void;
  setRememberMe: (remember: boolean) => void;
  setTokens: (token: string, refreshToken: string) => void;
  logout: () => void;
  updateUser: (user: Partial<User>) => void;
  getRole: () => string | null;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,
      rememberMe: false,
      isLoading: false,

      setAuth: (user, token, refreshToken, rememberMe = false) =>
        set({
          user,
          token,
          refreshToken,
          isAuthenticated: true,
          rememberMe,
        }),

      setLoading: (loading) =>
        set({ isLoading: loading }),

      setRememberMe: (remember) =>
        set({ rememberMe: remember }),

      setTokens: (token, refreshToken) =>
        set({ token, refreshToken }),

      logout: () =>
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        }),

      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      getRole: () => get().user?.role ?? null,
    }),
    {
      name: "healthcare-auth",
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        rememberMe: state.rememberMe,
      }),
    },
  ),
);
