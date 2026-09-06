import { beforeEach, describe, expect, test } from "vitest";

import { useCatalogueStore } from "./catalogue";

beforeEach(() => {
  useCatalogueStore.getState().reset();
});

describe("catalogue store", () => {
  test("resets pagination when search or status changes", () => {
    useCatalogueStore.getState().setPage(4);
    useCatalogueStore.getState().setSearch("  Arrival  ");

    expect(useCatalogueStore.getState()).toMatchObject({
      search: "Arrival",
      page: 1,
    });

    useCatalogueStore.getState().setPage(2);
    useCatalogueStore.getState().setStatus("ARCHIVED");

    expect(useCatalogueStore.getState()).toMatchObject({
      status: "ARCHIVED",
      page: 1,
    });
  });

  test("stores the selected film", () => {
    useCatalogueStore.getState().setSelectedFilmId(42);
    expect(useCatalogueStore.getState().selectedFilmId).toBe(42);
  });
});
