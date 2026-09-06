import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Avatar, Button, Modal, Spin, Typography } from "antd";
import { useEffect, useRef, useState } from "react";

import { ApiError } from "../api/client";
import { archiveFilm, getFilm, unarchiveFilm } from "../api/films";
import { rateAuthor, rateFilm } from "../api/ratings";
import { canChangeFilmFromToken, useAuthStore } from "../store/auth";
import { localRating, posterUrl, statusLabels } from "./filmPresentation";
import { RatingPopover } from "./RatingPopover";

const { Paragraph, Text, Title } = Typography;

interface FilmDetailProps {
  filmId: number;
  backLabel?: string;
  isAuthenticated: boolean;
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

function archivalErrorMessage(error: unknown, isArchived: boolean): string {
  const action = isArchived ? "de désarchiver" : "d’archiver";
  if (error instanceof ApiError && error.status === 401) {
    return "Votre session a expiré. Reconnectez-vous pour continuer.";
  }
  if (error instanceof ApiError && error.status === 403) {
    return `Vous n’avez pas l’autorisation ${action} ce film.`;
  }
  return `Impossible ${action} ce film. Vérifiez votre connexion puis réessayez.`;
}

function ArrowBackIcon() {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 24 24"
      width="1em"
      height="1em"
      fill="currentColor"
    >
      <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.42-1.41L7.83 13H20v-2Z" />
    </svg>
  );
}

export function FilmDetail({
  filmId,
  backLabel = "Retour au catalogue",
  isAuthenticated,
  onBack,
}: FilmDetailProps) {
  const queryClient = useQueryClient();
  const archivalPending = useRef(false);
  const [isConfirmationOpen, setIsConfirmationOpen] = useState(false);
  const [successToast, setSuccessToast] = useState<string | null>(null);
  const canChangeFilm = useAuthStore((state) =>
    canChangeFilmFromToken(state.accessToken),
  );
  const filmQuery = useQuery({
    queryKey: ["films", "detail", filmId],
    queryFn: () => getFilm(filmId),
  });
  const archivalMutation = useMutation({
    mutationFn: (isArchived: boolean) =>
      isArchived ? unarchiveFilm(filmId) : archiveFilm(filmId),
    onSuccess: async (updatedFilm) => {
      queryClient.setQueryData(["films", "detail", filmId], updatedFilm);
      setIsConfirmationOpen(false);
      setSuccessToast(
        updatedFilm.is_archived ? "Film archivé" : "Film désarchivé",
      );
      await queryClient.invalidateQueries({
        queryKey: ["films"],
        refetchType: "none",
      });
    },
    onError: () => {
      setIsConfirmationOpen(false);
    },
    onSettled: () => {
      archivalPending.current = false;
    },
  });

  useEffect(() => {
    if (!successToast) {
      return;
    }
    const timeout = window.setTimeout(() => setSuccessToast(null), 4_000);
    return () => window.clearTimeout(timeout);
  }, [successToast]);

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
              <Button onClick={onBack}>{backLabel}</Button>
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
  const handleRated = (subject: string, score: number) => {
    setSuccessToast(`${subject} noté ${score} / 5`);
    void queryClient.invalidateQueries({
      queryKey: ["films", "detail", filmId],
    });
  };

  return (
    <main className="film-detail-page">
      <div
        className="film-detail-backdrop"
        style={imageUrl ? { backgroundImage: `url(${imageUrl})` } : undefined}
        aria-hidden
      />
      <header className="detail-navigation">
        <Button
          className="detail-back"
          icon={<ArrowBackIcon />}
          onClick={onBack}
        >
          {backLabel}
        </Button>
        {canChangeFilm ? (
          <Button
            danger={!film.is_archived}
            loading={archivalMutation.isPending}
            disabled={archivalMutation.isPending}
            onClick={() => {
              archivalMutation.reset();
              setIsConfirmationOpen(true);
            }}
          >
            {film.is_archived ? "Désarchiver" : "Archiver"}
          </Button>
        ) : null}
      </header>

      <Modal
        centered
        open={isConfirmationOpen}
        title={
          film.is_archived ? "Désarchiver ce film ?" : "Archiver ce film ?"
        }
        okText={film.is_archived ? "Désarchiver" : "Archiver"}
        cancelText="Annuler"
        confirmLoading={archivalMutation.isPending}
        cancelButtonProps={{ disabled: archivalMutation.isPending }}
        closable={!archivalMutation.isPending}
        keyboard={!archivalMutation.isPending}
        maskClosable={!archivalMutation.isPending}
        onCancel={() => setIsConfirmationOpen(false)}
        onOk={() => {
          if (archivalPending.current) {
            return;
          }
          archivalPending.current = true;
          archivalMutation.mutate(film.is_archived);
        }}
      >
        <Paragraph>
          {film.is_archived
            ? "Le film réapparaîtra dans le catalogue principal."
            : "Le film sera déplacé vers les films archivés."}
        </Paragraph>
      </Modal>

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
          {archivalMutation.isError ? (
            <Alert
              className="detail-action-alert"
              type="error"
              showIcon
              title="Action impossible"
              description={archivalErrorMessage(
                archivalMutation.error,
                film.is_archived,
              )}
            />
          ) : null}
          <Title>{film.title}</Title>

          <div className="detail-ratings" aria-label="Notes du film">
            <div>
              <Text className="rating-value">
                {localRating(film.local_rating)}
              </Text>
              <Text className="rating-label">Note Hoorcinema</Text>
              {isAuthenticated ? (
                <RatingPopover
                  label={`Noter ${film.title}`}
                  onRate={(score) => rateFilm(film.id, score)}
                  onRated={(score) => handleRated("Film", score)}
                />
              ) : null}
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
                    <div className="author-copy">
                      <Text className="author-name">{authorName(author)}</Text>
                      <Text className="author-rating">
                        {localRating(author.local_rating)}
                      </Text>
                      {isAuthenticated ? (
                        <RatingPopover
                          label={`Noter ${authorName(author)}`}
                          onRate={(score) => rateAuthor(author.id, score)}
                          onRated={(score) => handleRated("Auteur", score)}
                        />
                      ) : null}
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
      {successToast ? (
        <div className="detail-success-toast" role="status">
          <span aria-hidden>✓</span>
          {successToast}
        </div>
      ) : null}
    </main>
  );
}
