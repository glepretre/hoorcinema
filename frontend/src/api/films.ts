import { apiRequest } from "./client";
import type { Film, FilmListParams, PaginatedFilms } from "../types/film";

export function buildFilmListPath(params: FilmListParams): string {
  const query = new URLSearchParams({
    page: String(params.page),
    page_size: String(params.pageSize),
  });

  if (params.search) {
    query.set("search", params.search);
  }
  if (params.status) {
    query.set("status", params.status);
  }
  if (params.isArchived !== undefined) {
    query.set("is_archived", String(params.isArchived));
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

export function archiveFilm(id: number): Promise<Film> {
  return apiRequest(`/api/films/${id}/archive/`, {
    method: "PATCH",
    authenticated: true,
  });
}

export function unarchiveFilm(id: number): Promise<Film> {
  return apiRequest(`/api/films/${id}/unarchive/`, {
    method: "PATCH",
    authenticated: true,
  });
}
