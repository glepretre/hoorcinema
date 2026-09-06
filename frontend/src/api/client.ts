import { useAuthStore } from "../store/auth";

interface ApiErrorPayload {
  detail?: string;
  [field: string]: unknown;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly payload: ApiErrorPayload,
  ) {
    super(payload.detail ?? "La requête a échoué.");
  }
}

interface RequestOptions extends RequestInit {
  authenticated?: boolean;
}

interface TokenPair {
  access: string;
  refresh: string;
}

let refreshRequest: Promise<TokenPair> | null = null;

async function readPayload(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return undefined;
  }

  const contentType = response.headers.get("Content-Type") ?? "";
  if (!contentType.includes("application/json")) {
    return undefined;
  }

  return response.json();
}

async function send<T>(path: string, options: RequestOptions): Promise<T> {
  const {
    authenticated = false,
    headers: customHeaders,
    ...requestInit
  } = options;
  const headers = new Headers(customHeaders);
  const { accessToken } = useAuthStore.getState();

  if (requestInit.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (authenticated && accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }

  const response = await fetch(path, { ...requestInit, headers });
  const payload = await readPayload(response);

  if (!response.ok) {
    throw new ApiError(
      response.status,
      (payload as ApiErrorPayload | undefined) ?? {},
    );
  }

  return payload as T;
}

async function refreshTokens(): Promise<TokenPair> {
  if (refreshRequest) {
    return refreshRequest;
  }

  const { refreshToken, setTokens, clearTokens } = useAuthStore.getState();
  if (!refreshToken) {
    clearTokens();
    throw new ApiError(401, { detail: "Votre session a expiré." });
  }

  refreshRequest = send<TokenPair>("/api/auth/refresh/", {
    method: "POST",
    body: JSON.stringify({ refresh: refreshToken }),
  })
    .then((tokens) => {
      setTokens(tokens);
      return tokens;
    })
    .catch((error: unknown) => {
      clearTokens();
      throw error;
    })
    .finally(() => {
      refreshRequest = null;
    });

  return refreshRequest;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  try {
    return await send<T>(path, options);
  } catch (error) {
    if (
      !(error instanceof ApiError) ||
      error.status !== 401 ||
      !options.authenticated
    ) {
      throw error;
    }

    await refreshTokens();
    return send<T>(path, options);
  }
}
