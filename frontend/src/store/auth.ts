import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

interface AuthTokens {
  access: string;
  refresh: string;
}

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  setTokens: (tokens: AuthTokens) => void;
  clearTokens: () => void;
}

export function canChangeFilmFromToken(accessToken: string | null): boolean {
  if (!accessToken) {
    return false;
  }

  try {
    const payload = accessToken.split(".")[1];
    if (!payload) {
      return false;
    }
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(atob(base64)) as { can_change_film?: unknown };
    return decoded.can_change_film === true;
  } catch {
    return false;
  }
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      setTokens: ({ access, refresh }) =>
        set({ accessToken: access, refreshToken: refresh }),
      clearTokens: () => set({ accessToken: null, refreshToken: null }),
    }),
    {
      name: "hoorcinema-auth",
      // TODO: Replace localStorage with secure HttpOnly cookies before production.
      storage: createJSONStorage(() => localStorage),
      partialize: ({ accessToken, refreshToken }) => ({
        accessToken,
        refreshToken,
      }),
    },
  ),
);
