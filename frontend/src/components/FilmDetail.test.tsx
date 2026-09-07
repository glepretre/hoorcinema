import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { ApiError } from "../api/client";
import * as filmsApi from "../api/films";
import * as ratingsApi from "../api/ratings";
import { useAuthStore } from "../store/auth";
import type { Film } from "../types/film";
import { FilmDetail } from "./FilmDetail";

vi.mock("../api/films", () => ({
  addFavorite: vi.fn(),
  archiveFilm: vi.fn(),
  getFilm: vi.fn(),
  removeFavorite: vi.fn(),
  unarchiveFilm: vi.fn(),
}));

vi.mock("../api/ratings", () => ({
  rateAuthor: vi.fn(),
  rateFilm: vi.fn(),
}));

const film: Film = {
  id: 7,
  title: "Cinema Paradiso",
  description: "Un cinéaste se souvient de son enfance.",
  release_date: "1988-11-17",
  status: "Released",
  is_archived: false,
  is_favorite: false,
  authors: [
    {
      id: 2,
      username: "giuseppe_tornatore",
      first_name: "Giuseppe",
      last_name: "Tornatore",
      avatar: "",
      source: "TMDB",
      tmdb_id: 84,
      local_rating: "4.00",
    },
  ],
  source: "TMDB",
  tmdb_id: 11216,
  tmdb_vote_average: "8.40",
  tmdb_vote_count: 4500,
  poster_path: "/cinema-paradiso.jpg",
  local_rating: "4.50",
  created_at: "2026-01-01T10:00:00Z",
  updated_at: "2026-01-01T10:00:00Z",
};

function renderDetail(
  onBack = vi.fn(),
  backLabel?: string,
  isAuthenticated = true,
) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FilmDetail
        filmId={7}
        backLabel={backLabel}
        isAuthenticated={isAuthenticated}
        onBack={onBack}
        onLogin={vi.fn()}
      />
    </QueryClientProvider>,
  );
  return onBack;
}

function accessToken(canChangeFilm: boolean, canRate = true): string {
  return `header.${btoa(JSON.stringify({ can_change_film: canChangeFilm, can_rate: canRate }))}.signature`;
}

async function confirmAction(name: "Archiver" | "Désarchiver") {
  fireEvent.click(screen.getByRole("button", { name }));
  await screen.findByText(`${name} ce film ?`);
  const buttons = screen.getAllByRole("button", { name });
  fireEvent.click(buttons[buttons.length - 1]);
}

beforeEach(() => {
  useAuthStore.getState().setTokens({
    access: accessToken(true),
    refresh: "refresh-token",
  });
  vi.mocked(filmsApi.getFilm).mockResolvedValue(film);
  vi.mocked(filmsApi.archiveFilm).mockResolvedValue({
    ...film,
    is_archived: true,
  });
  vi.mocked(filmsApi.unarchiveFilm).mockResolvedValue({
    ...film,
    is_archived: false,
  });
  vi.mocked(filmsApi.addFavorite).mockResolvedValue({
    ...film,
    is_favorite: true,
  });
  vi.mocked(filmsApi.removeFavorite).mockResolvedValue();
  vi.mocked(ratingsApi.rateFilm).mockResolvedValue({
    id: 1,
    film: 7,
    score: 4,
  });
  vi.mocked(ratingsApi.rateAuthor).mockResolvedValue({
    id: 2,
    author: 2,
    score: 5,
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("film detail", () => {
  test("loads and presents the film information", async () => {
    renderDetail();

    expect(screen.getByText("Chargement du film…")).toBeTruthy();
    expect(
      await screen.findByRole("heading", { name: "Cinema Paradiso" }),
    ).toBeTruthy();
    expect(
      screen.getByText("Un cinéaste se souvient de son enfance."),
    ).toBeTruthy();
    expect(screen.getByText("4,5 / 5")).toBeTruthy();
    expect(screen.getByText("8,4 / 10")).toBeTruthy();
    expect(screen.getByText(/4[\s\u202f]500 votes/)).toBeTruthy();
    expect(screen.getByText("Giuseppe Tornatore")).toBeTruthy();
    expect(
      screen.getByAltText("Affiche de Cinema Paradiso").getAttribute("src"),
    ).toBe("https://image.tmdb.org/t/p/w500/cinema-paradiso.jpg");
  });

  test("returns to the catalogue", async () => {
    const onBack = renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    fireEvent.click(
      screen.getByRole("button", { name: /Retour au catalogue/ }),
    );

    expect(onBack).toHaveBeenCalledOnce();
  });

  test("rates the film from its rating popover", async () => {
    renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    fireEvent.click(
      screen.getByRole("button", { name: "Noter Cinema Paradiso" }),
    );
    expect(await screen.findByText("Noter Cinema Paradiso")).toBeTruthy();
    fireEvent.click(screen.getAllByRole("radio")[3]);

    await waitFor(() => expect(ratingsApi.rateFilm).toHaveBeenCalledWith(7, 4));
    expect(await screen.findByText("Film noté 4 / 5")).toBeTruthy();
    expect(
      screen.getByRole("button", {
        name: "Noter Cinema Paradiso, note actuelle 4 sur 5",
      }),
    ).toBeTruthy();
    await waitFor(() => expect(filmsApi.getFilm).toHaveBeenCalledTimes(2));
  });

  test("rates an author from their card", async () => {
    renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    fireEvent.click(
      screen.getByRole("button", { name: "Noter Giuseppe Tornatore" }),
    );
    expect(await screen.findByText("Noter Giuseppe Tornatore")).toBeTruthy();
    fireEvent.click(screen.getAllByRole("radio")[4]);

    await waitFor(() =>
      expect(ratingsApi.rateAuthor).toHaveBeenCalledWith(2, 5),
    );
    expect(await screen.findByText("Auteur noté 5 / 5")).toBeTruthy();
    expect(
      screen.getByRole("button", {
        name: "Noter Giuseppe Tornatore, note actuelle 5 sur 5",
      }),
    ).toBeTruthy();
  });

  test("adds and removes the film from favorites", async () => {
    renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    fireEvent.click(
      screen.getByRole("button", { name: "Ajouter aux favoris" }),
    );

    await waitFor(() => expect(filmsApi.addFavorite).toHaveBeenCalledWith(7));
    expect(await screen.findByText("Film ajouté aux favoris")).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", { name: "Retirer des favoris" }),
    );

    await waitFor(() =>
      expect(filmsApi.removeFavorite).toHaveBeenCalledWith(7),
    );
    expect(await screen.findByText("Film retiré des favoris")).toBeTruthy();
  });

  test("uses the provided archived catalogue return label", async () => {
    renderDetail(vi.fn(), "Retour aux films archivés");
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    expect(
      screen.getByRole("button", { name: /Retour aux films archivés/ }),
    ).toBeTruthy();
  });

  test("shows a dedicated not-found state", async () => {
    vi.mocked(filmsApi.getFilm).mockRejectedValue(
      new ApiError(404, { detail: "Not found." }),
    );
    renderDetail();

    expect(await screen.findByText("Film introuvable")).toBeTruthy();
    expect(
      screen.getByText("Ce film n’existe pas ou n’est plus disponible."),
    ).toBeTruthy();
  });

  test("shows a retry action for other failures", async () => {
    vi.mocked(filmsApi.getFilm).mockRejectedValue(new Error("offline"));
    renderDetail();

    expect(
      await screen.findByText("Impossible de charger le film."),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: "Réessayer" })).toBeTruthy();
  });

  test("hides archival actions without the film change capability", async () => {
    useAuthStore.getState().setTokens({
      access: accessToken(false),
      refresh: "refresh-token",
    });
    renderDetail();

    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Désarchiver" })).toBeNull();
  });

  test("hides rating actions without the spectator capability", async () => {
    useAuthStore.getState().setTokens({
      access: accessToken(true, false),
      refresh: "refresh-token",
    });
    renderDetail();

    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    expect(screen.queryByRole("button", { name: /^Noter/ })).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Ajouter aux favoris" }),
    ).toBeNull();
    expect(screen.getByRole("button", { name: "Archiver" })).toBeTruthy();
  });

  test("hides all mutation actions from anonymous users", async () => {
    useAuthStore.getState().clearTokens();
    renderDetail(vi.fn(), undefined, false);

    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    expect(screen.queryByRole("button", { name: /^Noter/ })).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Ajouter aux favoris" }),
    ).toBeNull();
    expect(screen.queryByRole("button", { name: "Archiver" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Désarchiver" })).toBeNull();
    expect(ratingsApi.rateFilm).not.toHaveBeenCalled();
    expect(ratingsApi.rateAuthor).not.toHaveBeenCalled();
  });

  test("confirms archival, invalidates film caches, and offers unarchival", async () => {
    const invalidateQueries = vi.spyOn(
      QueryClient.prototype,
      "invalidateQueries",
    );
    const setTimeoutSpy = vi.spyOn(window, "setTimeout");
    renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    fireEvent.click(screen.getByRole("button", { name: "Archiver" }));
    expect(await screen.findByRole("dialog")).toBeTruthy();
    expect(document.querySelector(".ant-modal-centered")).toBeTruthy();
    const confirmationButtons = screen.getAllByRole("button", {
      name: "Archiver",
    });
    fireEvent.click(confirmationButtons[confirmationButtons.length - 1]);

    await waitFor(() => expect(filmsApi.archiveFilm).toHaveBeenCalledWith(7));
    expect(await screen.findByText("Film archivé")).toBeTruthy();
    expect(setTimeoutSpy).toHaveBeenCalledWith(expect.any(Function), 4_000);
    expect(screen.getByRole("button", { name: "Désarchiver" })).toBeTruthy();
    expect(invalidateQueries).toHaveBeenCalledWith({
      queryKey: ["films"],
      refetchType: "none",
    });
  });

  test("confirms unarchival for an archived film", async () => {
    vi.mocked(filmsApi.getFilm).mockResolvedValue({
      ...film,
      is_archived: true,
    });
    renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    await confirmAction("Désarchiver");

    await waitFor(() => expect(filmsApi.unarchiveFilm).toHaveBeenCalledWith(7));
    expect(await screen.findByText("Film désarchivé")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Archiver" })).toBeTruthy();
  });

  test("does not archive when confirmation is cancelled", async () => {
    renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    fireEvent.click(screen.getByRole("button", { name: "Archiver" }));
    await screen.findByText("Archiver ce film ?");
    fireEvent.click(screen.getByRole("button", { name: "Annuler" }));

    expect(filmsApi.archiveFilm).not.toHaveBeenCalled();
  });

  test("prevents another action while archival is pending", async () => {
    let resolveArchive: (value: Film) => void = () => undefined;
    vi.mocked(filmsApi.archiveFilm).mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveArchive = resolve;
        }),
    );
    renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    fireEvent.click(screen.getByRole("button", { name: "Archiver" }));
    await screen.findByText("Archiver ce film ?");
    const actions = screen.getAllByRole("button", { name: "Archiver" });
    const action = actions[0];
    const confirmation = actions[actions.length - 1];
    fireEvent.click(confirmation);
    fireEvent.click(confirmation);

    await waitFor(() => expect(action.hasAttribute("disabled")).toBe(true));
    expect(filmsApi.archiveFilm).toHaveBeenCalledOnce();
    resolveArchive({ ...film, is_archived: true });
    expect(await screen.findByText("Film archivé")).toBeTruthy();
  });

  test("shows a dedicated authorization error", async () => {
    vi.mocked(filmsApi.archiveFilm).mockRejectedValue(
      new ApiError(403, { detail: "Forbidden." }),
    );
    renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    await confirmAction("Archiver");

    expect(await screen.findByText("Action impossible")).toBeTruthy();
    expect(
      screen.getByText("Vous n’avez pas l’autorisation d’archiver ce film."),
    ).toBeTruthy();
  });

  test.each([
    [401, "Votre session a expiré. Reconnectez-vous pour continuer."],
    [
      500,
      "Impossible d’archiver ce film. Vérifiez votre connexion puis réessayez.",
    ],
  ])("shows the expected error for status %s", async (status, message) => {
    vi.mocked(filmsApi.archiveFilm).mockRejectedValue(
      new ApiError(status, { detail: "Request failed." }),
    );
    renderDetail();
    await screen.findByRole("heading", { name: "Cinema Paradiso" });

    await confirmAction("Archiver");

    expect(await screen.findByText(message)).toBeTruthy();
  });
});
