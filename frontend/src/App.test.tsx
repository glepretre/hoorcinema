import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import App from "./App";
import * as authApi from "./api/auth";
import { useAuthStore } from "./store/auth";

vi.mock("./api/auth", async (importOriginal) => {
  const original = await importOriginal<typeof import("./api/auth")>();
  return {
    ...original,
    registerSpectator: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  };
});

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: { retry: false },
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  useAuthStore.getState().clearTokens();
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("authentication screen", () => {
  test("shows registration first and switches between forms", () => {
    renderApp();

    expect(
      screen.getByRole("heading", { name: "Créer un compte" }),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Se connecter" }));
    expect(screen.getByRole("heading", { name: "Se connecter" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "S’inscrire" }));
    expect(
      screen.getByRole("heading", { name: "Créer un compte" }),
    ).toBeTruthy();
  });

  test("registers a spectator then opens the login form", async () => {
    vi.mocked(authApi.registerSpectator).mockResolvedValue({
      id: 1,
      username: "viewer",
      email: "viewer@example.com",
      first_name: "Cinema",
      last_name: "Viewer",
    });
    renderApp();

    fireEvent.change(screen.getByLabelText("Prénom"), {
      target: { value: "Cinema" },
    });
    fireEvent.change(screen.getByLabelText("Nom"), {
      target: { value: "Viewer" },
    });
    fireEvent.change(screen.getByLabelText("Nom d’utilisateur"), {
      target: { value: "viewer" },
    });
    fireEvent.change(screen.getByLabelText("Adresse e-mail"), {
      target: { value: "viewer@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Mot de passe"), {
      target: { value: "Secure-password-42" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Créer mon compte" }));

    await screen.findByText(
      "Votre compte a été créé. Vous pouvez maintenant vous connecter.",
    );
    expect(vi.mocked(authApi.registerSpectator).mock.calls[0]?.[0]).toEqual({
      username: "viewer",
      email: "viewer@example.com",
      first_name: "Cinema",
      last_name: "Viewer",
      password: "Secure-password-42",
    });
  });

  test("logs in and logs out while clearing the in-memory session", async () => {
    vi.mocked(authApi.login).mockImplementation(async () => {
      useAuthStore
        .getState()
        .setTokens({ access: "access-token", refresh: "refresh-token" });
    });
    vi.mocked(authApi.logout).mockImplementation(async () => {
      useAuthStore.getState().clearTokens();
    });
    renderApp();

    fireEvent.click(screen.getByRole("button", { name: "Se connecter" }));
    fireEvent.change(screen.getByLabelText("Nom d’utilisateur"), {
      target: { value: "viewer" },
    });
    fireEvent.change(screen.getByLabelText("Mot de passe"), {
      target: { value: "Secure-password-42" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Se connecter" }));

    await screen.findByRole("heading", {
      name: "Votre séance peut commencer.",
    });
    fireEvent.click(screen.getByRole("button", { name: "Se déconnecter" }));

    await screen.findByRole("heading", { name: "Créer un compte" });
    expect(useAuthStore.getState().accessToken).toBeNull();
  });

  test("shows a French message when login is rejected", async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error("Network failure"));
    renderApp();

    fireEvent.click(screen.getByRole("button", { name: "Se connecter" }));
    fireEvent.change(screen.getByLabelText("Nom d’utilisateur"), {
      target: { value: "viewer" },
    });
    fireEvent.change(screen.getByLabelText("Mot de passe"), {
      target: { value: "wrong-password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Se connecter" }));

    await waitFor(() =>
      expect(
        screen.getByText(
          "Impossible de contacter le service. Réessayez dans un instant.",
        ),
      ).toBeTruthy(),
    );
  });
});
