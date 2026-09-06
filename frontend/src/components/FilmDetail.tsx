import { useQuery } from "@tanstack/react-query";
import { Alert, Avatar, Button, Spin, Typography } from "antd";

import { ApiError } from "../api/client";
import { getFilm } from "../api/films";
import { localRating, posterUrl, statusLabels } from "./filmPresentation";

const { Paragraph, Text, Title } = Typography;

interface FilmDetailProps {
  filmId: number;
  onBack: () => void;
}

function authorName(author: {
  first_name: string;
  last_name: string;
  username: string;
}): string {
  return (
    [author.first_name, author.last_name].filter(Boolean).join(" ") ||
    author.username
  );
}

export function FilmDetail({ filmId, onBack }: FilmDetailProps) {
  const filmQuery = useQuery({
    queryKey: ["films", "detail", filmId],
    queryFn: () => getFilm(filmId),
  });

  if (filmQuery.isPending) {
    return (
      <main className="detail-state" role="status">
        <Spin size="large" />
        <Text className="text-on-dark">Chargement du film…</Text>
      </main>
    );
  }

  if (filmQuery.isError) {
    const notFound =
      filmQuery.error instanceof ApiError && filmQuery.error.status === 404;
    return (
      <main className="detail-state detail-error">
        <Alert
          type="error"
          showIcon
          title={
            notFound ? "Film introuvable" : "Impossible de charger le film."
          }
          description={
            notFound
              ? "Ce film n’existe pas ou n’est plus disponible."
              : "Vérifiez votre connexion puis réessayez."
          }
          action={
            notFound ? (
              <Button onClick={onBack}>Retour au catalogue</Button>
            ) : (
              <Button onClick={() => filmQuery.refetch()}>Réessayer</Button>
            )
          }
        />
      </main>
    );
  }

  const film = filmQuery.data;
  const imageUrl = posterUrl(film.poster_path, "w500");

  return (
    <main className="film-detail-page">
      <div
        className="film-detail-backdrop"
        style={imageUrl ? { backgroundImage: `url(${imageUrl})` } : undefined}
        aria-hidden
      />
      <header className="detail-navigation">
        <Button className="detail-back" onClick={onBack}>
          ← Retour au catalogue
        </Button>
      </header>

      <article className="film-detail-content">
        <div className="detail-poster-frame">
          {imageUrl ? (
            <img
              className="detail-poster"
              src={imageUrl}
              alt={`Affiche de ${film.title}`}
            />
          ) : (
            <div
              className="detail-poster detail-poster-placeholder"
              aria-hidden
            >
              <span>HC</span>
            </div>
          )}
        </div>

        <div className="detail-copy">
          <Title>{film.title}</Title>

          <div className="detail-ratings" aria-label="Notes du film">
            <div>
              <Text className="rating-value">
                {localRating(film.local_rating)}
              </Text>
              <Text className="rating-label">Note Hoorcinema</Text>
            </div>
            <div>
              <Text className="rating-value">
                {film.tmdb_vote_average
                  ? `${Number(film.tmdb_vote_average).toLocaleString("fr-FR")} / 10`
                  : "Non noté"}
              </Text>
              <Text className="rating-label">
                Note TMDb
                {film.tmdb_vote_count > 0
                  ? ` · ${film.tmdb_vote_count.toLocaleString("fr-FR")} votes`
                  : ""}
              </Text>
            </div>
          </div>

          <section
            className="detail-description"
            aria-labelledby="film-story-title"
          >
            <Text className="detail-section-label">L’histoire</Text>
            <Paragraph
              id="film-story-title"
              className="film-story-title text-on-dark"
            >
              {film.description ||
                "Aucun synopsis n’est disponible pour ce film."}
            </Paragraph>
          </section>

          <section
            className="detail-authors"
            aria-labelledby="film-authors-title"
          >
            <Text id="film-authors-title" className="detail-section-label">
              Auteurs
            </Text>
            {film.authors.length > 0 ? (
              <div className="author-list">
                {film.authors.map((author) => (
                  <div className="author-card" key={author.id}>
                    <Avatar src={author.avatar || undefined}>
                      {authorName(author).slice(0, 1).toUpperCase()}
                    </Avatar>
                    <div>
                      <Text className="author-name">{authorName(author)}</Text>
                      <Text className="author-rating">
                        {localRating(author.local_rating)}
                      </Text>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <Text className="detail-muted">Aucun auteur renseigné.</Text>
            )}
          </section>

          <dl className="detail-metadata">
            <div>
              <dt>Origine</dt>
              <dd>
                {film.source === "TMDB" ? "Import TMDb" : "Création locale"}
              </dd>
            </div>
            <div>
              <dt>Statut</dt>
              <dd>{statusLabels[film.status]}</dd>
            </div>
            <div>
              <dt>Année</dt>
              <dd>{film.release_date?.slice(0, 4) || "Inconnue"}</dd>
            </div>
          </dl>
        </div>
      </article>
    </main>
  );
}
