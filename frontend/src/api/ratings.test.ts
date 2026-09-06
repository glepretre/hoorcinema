import { describe, expect, test, vi } from "vitest";

import { apiRequest } from "./client";
import { rateAuthor, rateFilm } from "./ratings";

vi.mock("./client", () => ({ apiRequest: vi.fn() }));

describe("rating API", () => {
  test.each([
    [rateFilm, "/api/films/42/rating/"],
    [rateAuthor, "/api/authors/42/rating/"],
  ])("sends an authenticated rating", (rate, path) => {
    rate(42, 4);

    expect(apiRequest).toHaveBeenCalledWith(path, {
      method: "PUT",
      authenticated: true,
      body: JSON.stringify({ score: 4 }),
    });
  });
});
