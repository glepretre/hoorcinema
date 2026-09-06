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
