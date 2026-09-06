import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import * as filmsApi from "../api/films";
import { useCatalogueStore } from "../store/catalogue";
import type { Film, PaginatedFilms } from "../types/film";
import { FilmCatalogue } from "./FilmCatalogue";

vi.mock("../api/films", () => ({ getFilms: vi.fn() }));

const film: Film = {
  id: 7,
  title: "Cinema Paradiso",
  description: "A filmmaker remembers his childhood.",
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

const response: PaginatedFilms = {
  count: 1,
  next: null,
  previous: null,
  results: [film],
};

function renderCatalogue() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <FilmCatalogue onLogout={vi.fn()} />
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  useCatalogueStore.getState().reset();
  vi.mocked(filmsApi.getFilms).mockResolvedValue(response);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("film catalogue", () => {
  test("renders films with poster thumbnails and selects an accessible row", async () => {
    renderCatalogue();

    expect(screen.getByText("Chargement des films…")).toBeTruthy();
    expect(await screen.findByText("Cinema Paradiso")).toBeTruthy();
    expect(
      screen
        .getByText("Parcourez la collection, des nouveautés aux classiques.")
        .classList.contains("text-on-dark"),
    ).toBe(true);
    expect(
      screen.getByAltText("Affiche de Cinema Paradiso").getAttribute("src"),
    ).toBe("https://image.tmdb.org/t/p/w185/cinema-paradiso.jpg");
    expect(
      screen.getByText(
        (_, element) =>
          element?.classList.contains("film-mobile-meta") ?? false,
      ).textContent,
    ).toContain("1988 · 4,5 / 5");

    fireEvent.keyDown(screen.getByLabelText("Voir Cinema Paradiso"), {
      key: "Enter",
    });
    expect(useCatalogueStore.getState().selectedFilmId).toBe(7);
  });

  test("sends search, status, and ordering parameters while resetting the page", async () => {
    useCatalogueStore.getState().setPage(3);
    renderCatalogue();
    await screen.findByText("Cinema Paradiso");

    const search = screen.getByLabelText("Rechercher un film");
    fireEvent.change(search, { target: { value: "  paradis  " } });
    fireEvent.click(screen.getByRole("button", { name: "Rechercher" }));

    await waitFor(() =>
      expect(filmsApi.getFilms).toHaveBeenLastCalledWith({
        page: 1,
        search: "paradis",
        status: undefined,
        ordering: "title",
      }),
    );

    fireEvent.mouseDown(screen.getByLabelText("Filtrer par statut"));
    fireEvent.click(await screen.findByText("En post-production"));
    await waitFor(() =>
      expect(filmsApi.getFilms).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 1, status: "Post Production" }),
      ),
    );

    fireEvent.mouseDown(screen.getByLabelText("Trier les films"));
    fireEvent.click(await screen.findByText("Note (meilleure)"));
    await waitFor(() =>
      expect(filmsApi.getFilms).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 1, ordering: "-local_rating" }),
      ),
    );
  });

  test("requests the selected pagination page", async () => {
    vi.mocked(filmsApi.getFilms).mockResolvedValue({ ...response, count: 21 });
    renderCatalogue();
    await screen.findByText("Cinema Paradiso");

    fireEvent.click(screen.getByTitle("2"));

    await waitFor(() =>
      expect(filmsApi.getFilms).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2 }),
      ),
    );
  });

  test("shows French empty and error states", async () => {
    vi.mocked(filmsApi.getFilms).mockResolvedValueOnce({
      ...response,
      count: 0,
      results: [],
    });
    const { unmount } = renderCatalogue();
    expect(
      await screen.findByText("Aucun film ne correspond à votre recherche."),
    ).toBeTruthy();
    unmount();

    vi.mocked(filmsApi.getFilms).mockRejectedValueOnce(new Error("offline"));
    renderCatalogue();
    expect(
      await screen.findByText("Impossible de charger le catalogue."),
    ).toBeTruthy();
  });
});
