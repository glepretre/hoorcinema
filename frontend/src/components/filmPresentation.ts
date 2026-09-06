import type { FilmStatus } from "../types/film";

const POSTER_BASE_URL = "https://image.tmdb.org/t/p";

export const statusLabels: Record<FilmStatus, string> = {
  Rumored: "Rumeur",
  Planned: "Prévu",
  "In Production": "En production",
  "Post Production": "En post-production",
  Released: "Sorti",
  Canceled: "Annulé",
};

export const statusColors: Record<FilmStatus, string> = {
  Rumored: "purple",
  Planned: "blue",
  "In Production": "cyan",
  "Post Production": "geekblue",
  Released: "green",
  Canceled: "default",
};

export function posterUrl(
  path: string,
  size: "w185" | "w500" = "w185",
): string | undefined {
  if (!path) {
    return undefined;
  }
  return path.startsWith("http") ? path : `${POSTER_BASE_URL}/${size}${path}`;
}

export function releaseYear(date: string | null): string {
  return date ? date.slice(0, 4) : "Date inconnue";
}

export function localRating(rating: string | null): string {
  return rating ? `${Number(rating).toLocaleString("fr-FR")} / 5` : "Non noté";
}
