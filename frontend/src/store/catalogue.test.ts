import { beforeEach, describe, expect, test } from "vitest";

import { useCatalogueStore } from "./catalogue";

beforeEach(() => {
  localStorage.clear();
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
    useCatalogueStore.getState().setStatus("Canceled");

    expect(useCatalogueStore.getState()).toMatchObject({
      status: "Canceled",
      page: 1,
    });
  });

  test("stores the selected film", () => {
    useCatalogueStore.getState().setSelectedFilmId(42);
    expect(useCatalogueStore.getState().selectedFilmId).toBe(42);
  });

  test("persists the page size preference and resets the current page", () => {
    useCatalogueStore.getState().setPage(4);
    useCatalogueStore.getState().setPageSize(50);

    expect(useCatalogueStore.getState()).toMatchObject({
      page: 1,
      pageSize: 50,
    });
    expect(
      JSON.parse(
        localStorage.getItem("hoorcinema-catalogue-preferences") ?? "",
      ),
    ).toMatchObject({ state: { pageSize: 50 } });
  });
});
