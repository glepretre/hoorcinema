import { describe, expect, test, vi } from "vitest";

import { buildFilmListPath, getFilm } from "./films";
import { apiRequest } from "./client";

vi.mock("./client", () => ({ apiRequest: vi.fn() }));

describe("film API", () => {
  test("builds the paginated catalogue query", () => {
    expect(
      buildFilmListPath({
        page: 3,
        search: "Cinéma Paradiso",
        status: "In Production",
        ordering: "-local_rating",
      }),
    ).toBe(
      "/api/films/?page=3&search=Cin%C3%A9ma+Paradiso&status=In+Production&ordering=-local_rating",
    );
  });

  test("omits inactive filters", () => {
    expect(buildFilmListPath({ page: 1 })).toBe("/api/films/?page=1");
  });

  test("requests one film by its identifier", () => {
    getFilm(42);

    expect(apiRequest).toHaveBeenCalledWith("/api/films/42/");
  });
});
