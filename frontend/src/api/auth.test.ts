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
  test("trims profile fields before registration", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse({ id: 4, username: "viewer" }, 201));
    const data = {
      username: "  viewer  ",
      email: " viewer@example.com ",
      first_name: " Cinema ",
      last_name: " Viewer ",
      password: " Secure-password-42 ",
    };

    await registerSpectator(data);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/register/",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          username: "viewer",
          email: "viewer@example.com",
          first_name: "Cinema",
          last_name: "Viewer",
          password: " Secure-password-42 ",
        }),
      }),
    );
  });

  test("trims the login username and persists tokens", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse({ access: "access-token", refresh: "refresh-token" }),
      );

    await login({ username: "  Viewer  ", password: " Secure-password-42 " });

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/login/",
      expect.objectContaining({
        body: JSON.stringify({
          username: "Viewer",
          password: " Secure-password-42 ",
        }),
      }),
    );
    expect(useAuthStore.getState()).toEqual(
      expect.objectContaining({
        accessToken: "access-token",
        refreshToken: "refresh-token",
      }),
    );
    expect(JSON.parse(localStorage.getItem("hoorcinema-auth") ?? "")).toEqual({
      state: {
        accessToken: "access-token",
        refreshToken: "refresh-token",
      },
      version: 0,
    });
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
    expect(JSON.parse(localStorage.getItem("hoorcinema-auth") ?? "")).toEqual({
      state: { accessToken: null, refreshToken: null },
      version: 0,
    });
  });
});
