import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Empty,
  Input,
  Select,
  Spin,
  Table,
  Tag,
  Typography,
  type TableColumnsType,
} from "antd";
import { useMemo, useState } from "react";

import { getFilms } from "../api/films";
import { useCatalogueStore } from "../store/catalogue";
import type { Film, FilmOrdering, FilmStatus } from "../types/film";

const { Paragraph, Text, Title } = Typography;
const POSTER_BASE_URL = "https://image.tmdb.org/t/p/w185";

const statusLabels: Record<FilmStatus, string> = {
  Rumored: "Rumeur",
  Planned: "Prévu",
  "In Production": "En production",
  "Post Production": "En post-production",
  Released: "Sorti",
  Canceled: "Annulé",
};

const statusColors: Record<FilmStatus, string> = {
  Rumored: "purple",
  Planned: "blue",
  "In Production": "cyan",
  "Post Production": "geekblue",
  Released: "green",
  Canceled: "default",
};

function posterUrl(path: string): string | undefined {
  if (!path) {
    return undefined;
  }
  return path.startsWith("http") ? path : `${POSTER_BASE_URL}${path}`;
}

function releaseYear(date: string | null): string {
  return date ? date.slice(0, 4) : "Date inconnue";
}

function localRating(rating: string | null): string {
  return rating ? `${Number(rating).toLocaleString("fr-FR")} / 5` : "Non noté";
}

interface FilmCatalogueProps {
  isLoggingOut?: boolean;
  onLogout: () => void;
}

export function FilmCatalogue({
  isLoggingOut = false,
  onLogout,
}: FilmCatalogueProps) {
  const search = useCatalogueStore((state) => state.search);
  const status = useCatalogueStore((state) => state.status);
  const page = useCatalogueStore((state) => state.page);
  const setSearch = useCatalogueStore((state) => state.setSearch);
  const setStatus = useCatalogueStore((state) => state.setStatus);
  const setPage = useCatalogueStore((state) => state.setPage);
  const setSelectedFilmId = useCatalogueStore(
    (state) => state.setSelectedFilmId,
  );
  const [ordering, setOrdering] = useState<FilmOrdering>("title");
  const params = useMemo(
    () => ({ page, search: search || undefined, status, ordering }),
    [ordering, page, search, status],
  );
  const filmsQuery = useQuery({
    queryKey: ["films", params],
    queryFn: () => getFilms(params),
  });
  const columns = useMemo<TableColumnsType<Film>>(
    () => [
      {
        title: "Film",
        key: "film",
        render: (_, film) => (
          <div className="film-cell">
            {posterUrl(film.poster_path) ? (
              <img
                className="film-poster"
                src={posterUrl(film.poster_path)}
                alt={`Affiche de ${film.title}`}
              />
            ) : (
              <div className="film-poster film-poster-placeholder" aria-hidden>
                <span>HC</span>
              </div>
            )}
            <div>
              <Text className="film-title">{film.title}</Text>
              <Text className="film-mobile-meta">
                {releaseYear(film.release_date)} ·{" "}
                {localRating(film.local_rating)}
              </Text>
            </div>
          </div>
        ),
      },
      {
        title: "Sortie",
        dataIndex: "release_date",
        key: "release_date",
        width: 130,
        responsive: ["sm"],
        render: (date: string | null) => releaseYear(date),
      },
      {
        title: "Note locale",
        dataIndex: "local_rating",
        key: "local_rating",
        width: 150,
        responsive: ["md"],
        render: (rating: string | null) => localRating(rating),
      },
      {
        title: "Statut",
        dataIndex: "status",
        key: "status",
        width: 170,
        responsive: ["sm"],
        render: (filmStatus: FilmStatus) => (
          <Tag color={statusColors[filmStatus]}>{statusLabels[filmStatus]}</Tag>
        ),
      },
    ],
    [],
  );

  return (
    <main className="catalogue-page">
      <header className="catalogue-header">
        <div>
          <Text className="eyebrow">HOORCINEMA</Text>
          <Title>Films à l’affiche</Title>
          <Paragraph>
            Parcourez la collection, des nouveautés aux classiques.
          </Paragraph>
        </div>
        <Button loading={isLoggingOut} onClick={onLogout}>
          Se déconnecter
        </Button>
      </header>

      <section className="catalogue-content" aria-labelledby="catalogue-title">
        <div className="catalogue-heading">
          <div>
            <Text className="section-number">01 / CATALOGUE</Text>
            <Title id="catalogue-title" level={2}>
              La sélection
            </Title>
          </div>
          {filmsQuery.data && (
            <Text className="film-count">
              {filmsQuery.data.count} film
              {filmsQuery.data.count > 1 ? "s" : ""}
            </Text>
          )}
        </div>

        <div className="catalogue-controls">
          <Input.Search
            aria-label="Rechercher un film"
            allowClear
            defaultValue={search}
            enterButton="Rechercher"
            placeholder="Titre du film"
            onSearch={setSearch}
          />
          <Select<FilmStatus | undefined>
            aria-label="Filtrer par statut"
            allowClear
            placeholder="Tous les statuts"
            value={status}
            options={Object.entries(statusLabels).map(([value, label]) => ({
              value: value as FilmStatus,
              label,
            }))}
            onChange={setStatus}
          />
          <Select<FilmOrdering>
            aria-label="Trier les films"
            value={ordering}
            options={[
              { value: "title", label: "Titre (A–Z)" },
              { value: "-release_date", label: "Sortie (plus récente)" },
              { value: "release_date", label: "Sortie (plus ancienne)" },
              { value: "-local_rating", label: "Note (meilleure)" },
              { value: "local_rating", label: "Note (moins bonne)" },
            ]}
            onChange={(value) => {
              setOrdering(value);
              setPage(1);
            }}
          />
        </div>

        {filmsQuery.isPending ? (
          <div className="catalogue-state" role="status">
            <Spin size="large" />
            <Text>Chargement des films…</Text>
          </div>
        ) : filmsQuery.isError ? (
          <Alert
            type="error"
            showIcon
            title="Impossible de charger le catalogue."
            description="Vérifiez votre connexion puis réessayez."
            action={
              <Button onClick={() => filmsQuery.refetch()}>Réessayer</Button>
            }
          />
        ) : (
          <Table<Film>
            className="films-table"
            rowKey="id"
            columns={columns}
            dataSource={filmsQuery.data.results}
            locale={{
              emptyText: (
                <Empty description="Aucun film ne correspond à votre recherche." />
              ),
            }}
            pagination={{
              current: page,
              pageSize: 10,
              total: filmsQuery.data.count,
              showSizeChanger: false,
              hideOnSinglePage: true,
              onChange: setPage,
            }}
            scroll={{ x: 560 }}
            onRow={(film) => ({
              onClick: () => setSelectedFilmId(film.id),
              tabIndex: 0,
              onKeyDown: (event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setSelectedFilmId(film.id);
                }
              },
              "aria-label": `Voir ${film.title}`,
            })}
          />
        )}
      </section>
    </main>
  );
}
