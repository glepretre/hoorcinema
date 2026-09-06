import { apiRequest } from "./client";
import type { Film, FilmListParams, PaginatedFilms } from "../types/film";

export function buildFilmListPath(params: FilmListParams): string {
  const query = new URLSearchParams({ page: String(params.page) });

  if (params.search) {
    query.set("search", params.search);
  }
  if (params.status) {
    query.set("status", params.status);
  }
  if (params.ordering) {
    query.set("ordering", params.ordering);
  }

  return `/api/films/?${query.toString()}`;
}

export function getFilms(params: FilmListParams): Promise<PaginatedFilms> {
  return apiRequest(buildFilmListPath(params));
}

export function getFilm(id: number): Promise<Film> {
  return apiRequest(`/api/films/${id}/`);
}
