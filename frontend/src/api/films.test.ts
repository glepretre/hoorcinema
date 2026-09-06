import { describe, expect, test } from "vitest";

import { buildFilmListPath } from "./films";

describe("film API", () => {
  test("builds the paginated catalogue query", () => {
    expect(
      buildFilmListPath({
        page: 3,
        search: "Cinéma Paradiso",
        status: "PUBLISHED",
        ordering: "-local_rating",
      }),
    ).toBe(
      "/api/films/?page=3&search=Cin%C3%A9ma+Paradiso&status=PUBLISHED&ordering=-local_rating",
    );
  });

  test("omits inactive filters", () => {
    expect(buildFilmListPath({ page: 1 })).toBe("/api/films/?page=1");
  });
});
