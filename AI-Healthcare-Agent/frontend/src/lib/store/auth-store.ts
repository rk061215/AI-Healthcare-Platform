import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { User } from "@/types";

const PERSIST_KEY = "healthcare-auth";

function setCookie(name: string, value: string, days: number) {
  if (typeof document === "undefined") return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function removeCookie(name: string) {
  if (typeof document === "undefined") return;
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Lax`;
}

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

      setAuth: (user, token, refreshToken, rememberMe = false) => {
        set({
          user,
          token,
          refreshToken,
          isAuthenticated: true,
          rememberMe,
        });
        setCookie(
          PERSIST_KEY,
          JSON.stringify({
            state: { user, token, refreshToken, isAuthenticated: true, rememberMe },
            version: 0,
          }),
          rememberMe ? 30 : 1,
        );
      },

      setLoading: (loading) =>
        set({ isLoading: loading }),

      setRememberMe: (remember) =>
        set({ rememberMe: remember }),

      setTokens: (token, refreshToken) => {
        set({ token, refreshToken });
        const s = get();
        setCookie(
          PERSIST_KEY,
          JSON.stringify({
            state: {
              user: s.user,
              token,
              refreshToken,
              isAuthenticated: s.isAuthenticated,
              rememberMe: s.rememberMe,
            },
            version: 0,
          }),
          s.rememberMe ? 30 : 1,
        );
      },

      logout: () => {
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false,
        });
        removeCookie(PERSIST_KEY);
      },

      updateUser: (updates) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      getRole: () => get().user?.role ?? null,
    }),
    {
      name: PERSIST_KEY,
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
        rememberMe: state.rememberMe,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.isAuthenticated) {
          setCookie(
            PERSIST_KEY,
            JSON.stringify({ state, version: 0 }),
            state.rememberMe ? 30 : 1,
          );
        }
      },
    },
  ),
);
