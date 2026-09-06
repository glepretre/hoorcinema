import { create } from "zustand";

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

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  setTokens: ({ access, refresh }) =>
    set({ accessToken: access, refreshToken: refresh }),
  clearTokens: () => set({ accessToken: null, refreshToken: null }),
}));
