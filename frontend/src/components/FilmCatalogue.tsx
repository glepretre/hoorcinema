import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  ConfigProvider,
  Empty,
  Input,
  Pagination,
  Select,
  Spin,
  Table,
  Tag,
  Typography,
  type ThemeConfig,
  type TableColumnsType,
} from "antd";
import { useMemo, useState } from "react";

import { getFilms } from "../api/films";
import { useCatalogueStore } from "../store/catalogue";
import type {
  Film,
  FilmOrdering,
  FilmPageSize,
  FilmStatus,
} from "../types/film";
import {
  localRating,
  posterUrl,
  releaseYear,
  statusLabels,
  statusTagStyles,
} from "./filmPresentation";

const { Paragraph, Text, Title } = Typography;
const catalogueControlsTheme: ThemeConfig = {
  token: {
    colorBorder: "#746b63",
    colorTextPlaceholder: "#746b63",
  },
  components: {
    Input: {
      activeBorderColor: "#d85b36",
      hoverBorderColor: "#746b63",
    },
    Select: {
      activeBorderColor: "#d85b36",
      hoverBorderColor: "#746b63",
    },
  },
};

interface FilmCatalogueProps {
  isArchived: boolean;
  isLoggingOut?: boolean;
  onChangeCatalogue: () => void;
  onLogout: () => void;
  onSelectFilm: (filmId: number) => void;
}

export function FilmCatalogue({
  isArchived,
  isLoggingOut = false,
  onChangeCatalogue,
  onLogout,
  onSelectFilm,
}: FilmCatalogueProps) {
  const search = useCatalogueStore((state) => state.search);
  const status = useCatalogueStore((state) => state.status);
  const page = useCatalogueStore((state) => state.page);
  const pageSize = useCatalogueStore((state) => state.pageSize);
  const setSearch = useCatalogueStore((state) => state.setSearch);
  const setStatus = useCatalogueStore((state) => state.setStatus);
  const setPage = useCatalogueStore((state) => state.setPage);
  const setPageSize = useCatalogueStore((state) => state.setPageSize);
  const [ordering, setOrdering] = useState<FilmOrdering>("title");
  const params = useMemo(
    () => ({
      page,
      pageSize,
      isArchived,
      search: search || undefined,
      status,
      ordering,
    }),
    [isArchived, ordering, page, pageSize, search, status],
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
          <Tag style={statusTagStyles[filmStatus]}>
            {statusLabels[filmStatus]}
          </Tag>
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
          <Title>{isArchived ? "Films archivés" : "Films à l’affiche"}</Title>
          <Paragraph className="text-on-dark">
            {isArchived
              ? "Retrouvez les films conservés dans les archives."
              : "Parcourez la collection, des nouveautés aux classiques."}
          </Paragraph>
        </div>
        <div className="catalogue-header-actions">
          <Button loading={isLoggingOut} onClick={onLogout}>
            Se déconnecter
          </Button>
        </div>
      </header>

      <section className="catalogue-content" aria-labelledby="catalogue-title">
        <div className="catalogue-heading">
          <div>
            <Text className="section-number">
              {isArchived ? "02 / ARCHIVES" : "01 / CATALOGUE"}
            </Text>
            <Title id="catalogue-title" level={2}>
              {isArchived ? "La collection archivée" : "La sélection"}
            </Title>
          </div>
          <div className="catalogue-heading-actions">
            {filmsQuery.data && (
              <Text className="film-count">
                {filmsQuery.data.count} film
                {filmsQuery.data.count > 1 ? "s" : ""}
              </Text>
            )}
            <Button onClick={onChangeCatalogue}>
              {isArchived ? "Retour au catalogue" : "Films archivés"}
            </Button>
          </div>
        </div>

        <ConfigProvider theme={catalogueControlsTheme}>
          <div className="catalogue-controls">
            <div className="catalogue-control catalogue-search-control">
              <label htmlFor="catalogue-search">Recherche</label>
              <Input.Search
                id="catalogue-search"
                aria-label="Rechercher un film"
                allowClear
                defaultValue={search}
                enterButton="Rechercher"
                placeholder="Titre du film"
                onSearch={setSearch}
              />
            </div>
            <div className="catalogue-control">
              <label htmlFor="catalogue-status">Statut</label>
              <Select<FilmStatus | undefined>
                id="catalogue-status"
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
            </div>
            <div className="catalogue-control">
              <label htmlFor="catalogue-ordering">Trier par</label>
              <Select<FilmOrdering>
                id="catalogue-ordering"
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
          </div>
        </ConfigProvider>

        {filmsQuery.isPending ? (
          <div className="catalogue-state" role="status">
            <Spin size="large" />
            <Text>Chargement des films…</Text>
          </div>
        ) : filmsQuery.isError ? (
          <Alert
            type="error"
            showIcon
            title={
              isArchived
                ? "Impossible de charger les films archivés."
                : "Impossible de charger le catalogue."
            }
            description="Vérifiez votre connexion puis réessayez."
            action={
              <Button onClick={() => filmsQuery.refetch()}>Réessayer</Button>
            }
          />
        ) : (
          <div>
            <Table<Film>
              className="films-table"
              rowKey="id"
              columns={columns}
              dataSource={filmsQuery.data.results}
              locale={{
                emptyText: (
                  <Empty
                    description={
                      isArchived
                        ? "Aucun film archivé"
                        : "Aucun film ne correspond à votre recherche."
                    }
                  />
                ),
              }}
              pagination={false}
              scroll={{ x: 560 }}
              onRow={(film) => ({
                onClick: () => onSelectFilm(film.id),
                tabIndex: 0,
                onKeyDown: (event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelectFilm(film.id);
                  }
                },
                "aria-label": `Voir ${film.title}`,
              })}
            />
            <ConfigProvider theme={catalogueControlsTheme}>
              <div className="catalogue-pagination-bar">
                <div className="catalogue-control catalogue-page-size-control">
                  <label htmlFor="catalogue-page-size">Films par page</label>
                  <Select<FilmPageSize>
                    id="catalogue-page-size"
                    aria-label="Nombre de films par page"
                    value={pageSize}
                    options={[
                      { value: 10, label: "10 films" },
                      { value: 50, label: "50 films" },
                      { value: 100, label: "100 films" },
                    ]}
                    onChange={setPageSize}
                  />
                </div>
                {filmsQuery.data.count > pageSize && (
                  <div
                    className="catalogue-pagination-control"
                    role="group"
                    aria-labelledby="catalogue-pagination-label"
                  >
                    <span
                      id="catalogue-pagination-label"
                      className="catalogue-control-label"
                    >
                      Pages
                    </span>
                    <Pagination
                      current={page}
                      pageSize={pageSize}
                      total={filmsQuery.data.count}
                      showSizeChanger={false}
                      onChange={setPage}
                    />
                  </div>
                )}
              </div>
            </ConfigProvider>
          </div>
        )}
      </section>
    </main>
  );
}
