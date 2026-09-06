import { apiRequest } from "./client";
import { useAuthStore } from "../store/auth";

export interface RegistrationData {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}

export interface LoginData {
  username: string;
  password: string;
}

interface RegistrationResponse extends Omit<RegistrationData, "password"> {
  id: number;
}

interface TokenPair {
  access: string;
  refresh: string;
}

export function registerSpectator(
  data: RegistrationData,
): Promise<RegistrationResponse> {
  const normalizedData = {
    ...data,
    username: data.username.trim(),
    email: data.email.trim(),
    first_name: data.first_name.trim(),
    last_name: data.last_name.trim(),
  };

  return apiRequest("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify(normalizedData),
  });
}

export async function login(data: LoginData): Promise<void> {
  const tokens = await apiRequest<TokenPair>("/api/auth/login/", {
    method: "POST",
    body: JSON.stringify({ ...data, username: data.username.trim() }),
  });
  useAuthStore.getState().setTokens(tokens);
}

export async function logout(): Promise<void> {
  const { refreshToken, clearTokens } = useAuthStore.getState();

  try {
    if (refreshToken) {
      await apiRequest("/api/auth/logout/", {
        method: "POST",
        body: JSON.stringify({ refresh: refreshToken }),
      });
    }
  } catch {
    // Losing the in-memory token still closes the local session.
  } finally {
    clearTokens();
  }
}
