import { apiRequest } from "./client";

export interface Rating {
  id: number;
  score: number;
  film?: number;
  author?: number;
}

function saveRating(path: string, score: number): Promise<Rating> {
  return apiRequest(path, {
    method: "PUT",
    authenticated: true,
    body: JSON.stringify({ score }),
  });
}

export function rateFilm(id: number, score: number): Promise<Rating> {
  return saveRating(`/api/films/${id}/rating/`, score);
}

export function rateAuthor(id: number, score: number): Promise<Rating> {
  return saveRating(`/api/authors/${id}/rating/`, score);
}
