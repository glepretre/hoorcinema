export type FilmStatus =
  | "Rumored"
  | "Planned"
  | "In Production"
  | "Post Production"
  | "Released"
  | "Canceled";
export type FilmSource = "ADMIN" | "TMDB";
export type FilmPageSize = 10 | 50 | 100;
export type FilmOrdering =
  "title" | "release_date" | "-release_date" | "local_rating" | "-local_rating";

export interface AuthorSummary {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  avatar: string;
  source: FilmSource;
  tmdb_id: number | null;
  local_rating: string | null;
}

export interface Film {
  id: number;
  title: string;
  description: string;
  release_date: string | null;
  status: FilmStatus;
  is_archived: boolean;
  authors: AuthorSummary[];
  source: FilmSource;
  tmdb_id: number | null;
  tmdb_vote_average: string | null;
  tmdb_vote_count: number;
  poster_path: string;
  local_rating: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedFilms {
  count: number;
  next: string | null;
  previous: string | null;
  results: Film[];
}

export interface FilmListParams {
  page: number;
  pageSize: FilmPageSize;
  isArchived?: boolean;
  search?: string;
  status?: FilmStatus;
  ordering?: FilmOrdering;
}
