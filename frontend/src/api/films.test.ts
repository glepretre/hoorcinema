import { describe, expect, test, vi } from "vitest";

import {
  addFavorite,
  archiveFilm,
  buildFilmListPath,
  getFavoriteFilms,
  getFilm,
  removeFavorite,
  unarchiveFilm,
} from "./films";
import { apiRequest } from "./client";

vi.mock("./client", () => ({ apiRequest: vi.fn() }));

describe("film API", () => {
  test("builds the paginated catalogue query", () => {
    expect(
      buildFilmListPath({
        page: 3,
        pageSize: 50,
        search: "Cinéma Paradiso",
        status: "In Production",
        isArchived: true,
        ordering: "-local_rating",
      }),
    ).toBe(
      "/api/films/?page=3&page_size=50&search=Cin%C3%A9ma+Paradiso&status=In+Production&is_archived=true&ordering=-local_rating",
    );
  });

  test("includes the active films filter", () => {
    expect(
      buildFilmListPath({ page: 1, pageSize: 10, isArchived: false }),
    ).toBe("/api/films/?page=1&page_size=10&is_archived=false");
  });

  test("omits inactive filters", () => {
    expect(buildFilmListPath({ page: 1, pageSize: 10 })).toBe(
      "/api/films/?page=1&page_size=10",
    );
  });

  test("requests one film by its identifier", () => {
    getFilm(42);

    expect(apiRequest).toHaveBeenCalledWith("/api/films/42/", {
      authenticated: true,
    });
  });

  test("requests the authenticated paginated favorites", () => {
    getFavoriteFilms({
      page: 2,
      pageSize: 50,
      search: "paradis",
      status: "Released",
      ordering: "-release_date",
    });

    expect(apiRequest).toHaveBeenCalledWith(
      "/api/me/favorites/?page=2&page_size=50&search=paradis&status=Released&ordering=-release_date",
      { authenticated: true },
    );
  });

  test.each([
    [addFavorite, "POST"],
    [removeFavorite, "DELETE"],
  ])("sends an authenticated favorite mutation", (mutateFavorite, method) => {
    mutateFavorite(42);

    expect(apiRequest).toHaveBeenCalledWith("/api/films/42/favorite/", {
      method,
      authenticated: true,
    });
  });

  test.each([
    [archiveFilm, "/api/films/42/archive/"],
    [unarchiveFilm, "/api/films/42/unarchive/"],
  ])("sends an authenticated archival mutation", (mutateFilm, path) => {
    mutateFilm(42);

    expect(apiRequest).toHaveBeenCalledWith(path, {
      method: "PATCH",
      authenticated: true,
    });
  });
});
