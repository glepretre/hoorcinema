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

function capabilityFromToken(
  accessToken: string | null,
  capability: "can_change_film" | "can_rate",
): boolean {
  if (!accessToken) {
    return false;
  }

  try {
    const payload = accessToken.split(".")[1];
    if (!payload) {
      return false;
    }
    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");
    const decoded = JSON.parse(atob(base64)) as Record<string, unknown>;
    return decoded[capability] === true;
  } catch {
    return false;
  }
}

export function canChangeFilmFromToken(accessToken: string | null): boolean {
  return capabilityFromToken(accessToken, "can_change_film");
}

export function canRateFromToken(accessToken: string | null): boolean {
  return capabilityFromToken(accessToken, "can_rate");
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
