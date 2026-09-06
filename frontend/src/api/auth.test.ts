import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { login, logout, registerSpectator } from "./auth";
import { useAuthStore } from "../store/auth";

function jsonResponse(payload: unknown, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  useAuthStore.getState().clearTokens();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("authentication API", () => {
  test("sends registration data to the spectator endpoint", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: 4, username: "viewer" }, 201));
    const data = {
      username: "viewer",
      email: "viewer@example.com",
      first_name: "Cinema",
      last_name: "Viewer",
      password: "Secure-password-42",
    };

    await registerSpectator(data);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/register/",
      expect.objectContaining({ method: "POST", body: JSON.stringify(data) }),
    );
  });

  test("keeps login tokens in memory", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ access: "access-token", refresh: "refresh-token" }),
    );

    await login({ username: "viewer", password: "Secure-password-42" });

    expect(useAuthStore.getState()).toEqual(
      expect.objectContaining({
        accessToken: "access-token",
        refreshToken: "refresh-token",
      }),
    );
    expect(localStorage).toHaveLength(0);
    expect(sessionStorage).toHaveLength(0);
  });

  test("clears local tokens even when remote logout fails", async () => {
    useAuthStore
      .getState()
      .setTokens({ access: "access-token", refresh: "refresh-token" });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      jsonResponse({ detail: "Invalid token" }, 401),
    );

    await expect(logout()).resolves.toBeUndefined();
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().refreshToken).toBeNull();
  });
});
