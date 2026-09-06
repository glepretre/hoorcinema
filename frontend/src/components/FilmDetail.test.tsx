import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, test, vi } from "vitest";

import { ApiError } from "../api/client";
import * as filmsApi from "../api/films";
import type { Film } from "../types/film";
import { FilmDetail } from "./FilmDetail";

vi.mock("../api/films", () => ({ getFilm: vi.fn() }));

const film: Film = {
  id: 7,
  title: "Cinema Paradiso",
  description: "Un cinéaste se souvient de son enfance.",
  release_date: "1988-11-17",
  status: "Released",
  is_archived: false,
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

function renderDetail(onBack = vi.fn(), backLabel?: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <QueryClientProvider client={queryClient}>
      <FilmDetail filmId={7} backLabel={backLabel} onBack={onBack} />
    </QueryClientProvider>,
  );
  return onBack;
}

beforeEach(() => {
  vi.mocked(filmsApi.getFilm).mockResolvedValue(film);
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
});
