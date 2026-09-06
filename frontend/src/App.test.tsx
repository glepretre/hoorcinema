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
import * as filmsApi from "./api/films";
import { useAuthStore } from "./store/auth";
import { useCatalogueStore } from "./store/catalogue";
import type { Film } from "./types/film";

vi.mock("./api/auth", async (importOriginal) => {
  const original = await importOriginal<typeof import("./api/auth")>();
  return {
    ...original,
    registerSpectator: vi.fn(),
    login: vi.fn(),
    logout: vi.fn(),
  };
});

vi.mock("./api/films", () => ({
  archiveFilm: vi.fn(),
  getFilms: vi.fn(),
  getFilm: vi.fn(),
  unarchiveFilm: vi.fn(),
}));

const film: Film = {
  id: 7,
  title: "Cinema Paradiso",
  description: "Un cinéaste se souvient de son enfance.",
  release_date: "1988-11-17",
  status: "Released",
  is_archived: false,
  authors: [],
  source: "TMDB",
  tmdb_id: 11216,
  tmdb_vote_average: "8.40",
  tmdb_vote_count: 4500,
  poster_path: "/cinema-paradiso.jpg",
  local_rating: "4.50",
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-01T10:00:00Z",
};

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
  history.replaceState(null, "", "/");
  useAuthStore.getState().clearTokens();
  useCatalogueStore.getState().reset();
  vi.mocked(filmsApi.getFilms).mockResolvedValue({
    count: 0,
    next: null,
    previous: null,
    results: [],
  });
  vi.mocked(filmsApi.getFilm).mockResolvedValue(film);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("film navigation", () => {
  test("opens a film URL from the catalogue and returns", async () => {
    history.replaceState(null, "", "/films/");
    useAuthStore.getState().setTokens({ access: "access", refresh: "refresh" });
    vi.mocked(filmsApi.getFilms).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [film],
    });
    renderApp();

    fireEvent.click(await screen.findByLabelText("Voir Cinema Paradiso"));

    expect(location.pathname).toBe("/films/7/");
    expect(useCatalogueStore.getState().selectedFilmId).toBe(7);
    expect(
      await screen.findByRole("heading", { name: "Cinema Paradiso" }),
    ).toBeTruthy();

    fireEvent.click(
      screen.getByRole("button", { name: /Retour au catalogue/ }),
    );
    expect(location.pathname).toBe("/films/");
    expect(
      await screen.findByRole("heading", { name: "Films à l’affiche" }),
    ).toBeTruthy();
  });

  test("loads a film directly from its URL", async () => {
    history.replaceState(null, "", "/films/7/");
    useAuthStore.getState().setTokens({ access: "access", refresh: "refresh" });

    renderApp();

    expect(
      await screen.findByRole("heading", { name: "Cinema Paradiso" }),
    ).toBeTruthy();
    expect(filmsApi.getFilm).toHaveBeenCalledWith(7);
    expect(filmsApi.getFilms).not.toHaveBeenCalled();
    expect(useCatalogueStore.getState().selectedFilmId).toBe(7);
  });

  test("loads archived films directly and returns there from a detail", async () => {
    history.replaceState(null, "", "/films/archives/");
    useAuthStore.getState().setTokens({ access: "access", refresh: "refresh" });
    vi.mocked(filmsApi.getFilms).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [{ ...film, is_archived: true }],
    });

    renderApp();

    expect(
      await screen.findByRole("heading", { name: "Films archivés" }),
    ).toBeTruthy();
    expect(filmsApi.getFilms).toHaveBeenLastCalledWith(
      expect.objectContaining({ isArchived: true }),
    );

    fireEvent.click(await screen.findByLabelText("Voir Cinema Paradiso"));
    expect(location.pathname).toBe("/films/7/");
    fireEvent.click(
      await screen.findByRole("button", {
        name: /Retour aux films archivés/,
      }),
    );

    expect(location.pathname).toBe("/films/archives/");
    expect(
      await screen.findByRole("heading", { name: "Films archivés" }),
    ).toBeTruthy();
  });

  test("navigates between active and archived catalogues", async () => {
    history.replaceState(null, "", "/films/");
    useAuthStore.getState().setTokens({ access: "access", refresh: "refresh" });
    renderApp();

    await screen.findByRole("heading", { name: "Films à l’affiche" });
    expect(filmsApi.getFilms).toHaveBeenLastCalledWith(
      expect.objectContaining({ isArchived: false }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Films archivés" }));

    expect(location.pathname).toBe("/films/archives/");
    expect(
      await screen.findByRole("heading", { name: "Films archivés" }),
    ).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", { name: "Retour au catalogue" }),
    );
    expect(location.pathname).toBe("/films/");
  });

  test("lets an anonymous user browse the catalogue and film details", async () => {
    vi.mocked(filmsApi.getFilms).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [film],
    });
    renderApp();

    fireEvent.click(
      screen.getByRole("button", { name: "Accéder au catalogue" }),
    );

    expect(location.pathname).toBe("/films/");
    expect(await screen.findByText("Cinema Paradiso")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Se connecter" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Mon compte" })).toBeNull();

    fireEvent.click(screen.getByLabelText("Voir Cinema Paradiso"));

    expect(
      await screen.findByRole("heading", { name: "Cinema Paradiso" }),
    ).toBeTruthy();
    expect(screen.queryByRole("button", { name: /^Noter/ })).toBeNull();
    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
    expect(screen.getByRole("button", { name: "Se connecter" })).toBeTruthy();
  });

  test("sends an anonymous catalogue user to login", async () => {
    history.replaceState(null, "", "/films/");
    renderApp();

    await screen.findByRole("heading", { name: "Films à l’affiche" });
    fireEvent.click(screen.getByRole("button", { name: "Se connecter" }));

    expect(location.pathname).toBe("/login/");
    expect(screen.getByRole("heading", { name: "Se connecter" })).toBeTruthy();
  });
});

describe("authentication screen", () => {
  test("shows registration first and switches between forms", () => {
    renderApp();

    expect(
      screen
        .getByText(/Retrouvez les films qui vous marquent/)
        .classList.contains("text-on-dark"),
    ).toBe(true);
    expect(
      screen.getByRole("heading", { name: "Créer un compte" }),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Se connecter" }));
    expect(location.pathname).toBe("/login/");
    expect(screen.getByRole("heading", { name: "Se connecter" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "S’inscrire" }));
    expect(location.pathname).toBe("/");
    expect(
      screen.getByRole("heading", { name: "Créer un compte" }),
    ).toBeTruthy();
  });

  test("loads the login form directly from its URL", () => {
    history.replaceState(null, "", "/login/");

    renderApp();

    expect(screen.getByRole("heading", { name: "Se connecter" })).toBeTruthy();
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
    expect(location.pathname).toBe("/login/");
    expect(vi.mocked(authApi.registerSpectator).mock.calls[0]?.[0]).toEqual({
      username: "viewer",
      email: "viewer@example.com",
      first_name: "Cinema",
      last_name: "Viewer",
      password: "Secure-password-42",
    });
  });

  test("logs in and logs out while clearing the persisted session", async () => {
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

    await screen.findByRole("heading", { name: "Films à l’affiche" });
    expect(location.pathname).toBe("/films/");
    fireEvent.click(screen.getByRole("button", { name: "Mon compte" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Se déconnecter" }));

    await screen.findByRole("heading", { name: "Se connecter" });
    expect(location.pathname).toBe("/login/");
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
