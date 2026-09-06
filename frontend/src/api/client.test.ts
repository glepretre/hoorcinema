import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { ApiError, apiRequest } from "./client";
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

describe("authenticated API client", () => {
  test("rotates tokens and retries an expired request once", async () => {
    useAuthStore
      .getState()
      .setTokens({ access: "expired-access", refresh: "current-refresh" });
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ detail: "Expired" }, 401))
      .mockResolvedValueOnce(
        jsonResponse({ access: "new-access", refresh: "new-refresh" }),
      )
      .mockResolvedValueOnce(jsonResponse({ title: "Arrival" }));

    const film = await apiRequest<{ title: string }>("/api/films/1/", {
      authenticated: true,
    });

    expect(film.title).toBe("Arrival");
    expect(useAuthStore.getState()).toEqual(
      expect.objectContaining({
        accessToken: "new-access",
        refreshToken: "new-refresh",
      }),
    );
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/auth/refresh/",
      expect.objectContaining({
        body: JSON.stringify({ refresh: "current-refresh" }),
      }),
    );
    const retryHeaders = fetchMock.mock.calls[2]?.[1]?.headers as Headers;
    expect(retryHeaders.get("Authorization")).toBe("Bearer new-access");
  });

  test("shares one refresh between concurrent expired requests", async () => {
    useAuthStore
      .getState()
      .setTokens({ access: "expired-access", refresh: "current-refresh" });
    let protectedCalls = 0;
    let refreshCalls = 0;
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      if (input === "/api/auth/refresh/") {
        refreshCalls += 1;
        return jsonResponse({ access: "new-access", refresh: "new-refresh" });
      }
      protectedCalls += 1;
      return protectedCalls <= 2
        ? jsonResponse({ detail: "Expired" }, 401)
        : jsonResponse({ ok: true });
    });

    await Promise.all([
      apiRequest("/api/films/1/", { authenticated: true }),
      apiRequest("/api/me/favorites/", { authenticated: true }),
    ]);

    expect(refreshCalls).toBe(1);
  });

  test("does not refresh repeatedly when the retried request is rejected", async () => {
    useAuthStore
      .getState()
      .setTokens({ access: "expired-access", refresh: "current-refresh" });
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ detail: "Expired" }, 401))
      .mockResolvedValueOnce(
        jsonResponse({ access: "new-access", refresh: "new-refresh" }),
      )
      .mockResolvedValueOnce(jsonResponse({ detail: "Rejected" }, 401));

    await expect(
      apiRequest("/api/films/1/archive/", {
        method: "PATCH",
        authenticated: true,
      }),
    ).rejects.toBeInstanceOf(ApiError);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  test("clears the session when refresh is rejected", async () => {
    useAuthStore
      .getState()
      .setTokens({ access: "expired-access", refresh: "invalid-refresh" });
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse({ detail: "Expired" }, 401))
      .mockResolvedValueOnce(jsonResponse({ detail: "Invalid token" }, 401));

    await expect(
      apiRequest("/api/me/favorites/", { authenticated: true }),
    ).rejects.toBeInstanceOf(ApiError);
    expect(useAuthStore.getState().accessToken).toBeNull();
    expect(useAuthStore.getState().refreshToken).toBeNull();
  });
});
