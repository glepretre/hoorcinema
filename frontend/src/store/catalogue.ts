import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { FilmPageSize, FilmStatus } from "../types/film";

interface CatalogueState {
  search: string;
  status: FilmStatus | undefined;
  page: number;
  pageSize: FilmPageSize;
  selectedFilmId: number | null;
  setSearch: (search: string) => void;
  setStatus: (status: FilmStatus | undefined) => void;
  setPage: (page: number) => void;
  setPageSize: (pageSize: FilmPageSize) => void;
  setSelectedFilmId: (selectedFilmId: number | null) => void;
  reset: () => void;
}

const initialState = {
  search: "",
  status: undefined,
  page: 1,
  pageSize: 10 as FilmPageSize,
  selectedFilmId: null,
};

export const useCatalogueStore = create<CatalogueState>()(
  persist(
    (set) => ({
      ...initialState,
      setSearch: (search) => set({ search: search.trim(), page: 1 }),
      setStatus: (status) => set({ status, page: 1 }),
      setPage: (page) => set({ page }),
      setPageSize: (pageSize) => set({ pageSize, page: 1 }),
      setSelectedFilmId: (selectedFilmId) => set({ selectedFilmId }),
      reset: () => set(initialState),
    }),
    {
      name: "hoorcinema-catalogue-preferences",
      storage: createJSONStorage(() => localStorage),
      partialize: ({ pageSize }) => ({ pageSize }),
    },
  ),
);
