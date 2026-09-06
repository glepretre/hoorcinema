import { create } from "zustand";

import type { FilmStatus } from "../types/film";

interface CatalogueState {
  search: string;
  status: FilmStatus | undefined;
  page: number;
  selectedFilmId: number | null;
  setSearch: (search: string) => void;
  setStatus: (status: FilmStatus | undefined) => void;
  setPage: (page: number) => void;
  setSelectedFilmId: (selectedFilmId: number | null) => void;
  reset: () => void;
}

const initialState = {
  search: "",
  status: undefined,
  page: 1,
  selectedFilmId: null,
};

export const useCatalogueStore = create<CatalogueState>((set) => ({
  ...initialState,
  setSearch: (search) => set({ search: search.trim(), page: 1 }),
  setStatus: (status) => set({ status, page: 1 }),
  setPage: (page) => set({ page }),
  setSelectedFilmId: (selectedFilmId) => set({ selectedFilmId }),
  reset: () => set(initialState),
}));
