import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { logout } from "./api/auth";
import { AuthScreen } from "./components/AuthScreen";
import { FilmCatalogue } from "./components/FilmCatalogue";
import { FilmDetail } from "./components/FilmDetail";
import { useAuthStore } from "./store/auth";
import { useCatalogueStore } from "./store/catalogue";

const ARCHIVED_FILMS_PATH = "/films/archives/";

type CataloguePath = "/" | typeof ARCHIVED_FILMS_PATH;

interface AppRoute {
  cataloguePath: CataloguePath;
  filmId: number | null;
}

function isCataloguePath(value: unknown): value is CataloguePath {
  return value === "/" || value === ARCHIVED_FILMS_PATH;
}

function routeFromLocation(): AppRoute {
  const pathname = location.pathname;
  const match = pathname.match(/^\/films\/(\d+)\/?$/);
  if (match) {
    const cataloguePath = (history.state as { cataloguePath?: unknown } | null)
      ?.cataloguePath;
    return {
      cataloguePath: isCataloguePath(cataloguePath) ? cataloguePath : "/",
      filmId: Number(match[1]),
    };
  }
  return {
    cataloguePath: pathname === ARCHIVED_FILMS_PATH ? ARCHIVED_FILMS_PATH : "/",
    filmId: null,
  };
}

export default function App() {
  const isAuthenticated = useAuthStore((state) => state.accessToken !== null);
  const setSelectedFilmId = useCatalogueStore(
    (state) => state.setSelectedFilmId,
  );
  const [route, setRoute] = useState(routeFromLocation);
  const logoutMutation = useMutation({ mutationFn: logout });

  useEffect(() => {
    setSelectedFilmId(route.filmId);
  }, [route.filmId, setSelectedFilmId]);

  useEffect(() => {
    const handleNavigation = () => setRoute(routeFromLocation());
    window.addEventListener("popstate", handleNavigation);
    return () => window.removeEventListener("popstate", handleNavigation);
  }, []);

  const navigateToFilm = (selectedFilmId: number) => {
    history.pushState(
      { cataloguePath: route.cataloguePath },
      "",
      `/films/${selectedFilmId}/`,
    );
    setRoute({ ...route, filmId: selectedFilmId });
  };

  const navigateToCatalogue = (cataloguePath: CataloguePath) => {
    history.pushState(null, "", cataloguePath);
    useCatalogueStore.getState().setPage(1);
    setRoute({ cataloguePath, filmId: null });
  };

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  const isArchived = route.cataloguePath === ARCHIVED_FILMS_PATH;

  return route.filmId !== null ? (
    <FilmDetail
      filmId={route.filmId}
      backLabel={isArchived ? "Retour aux films archivés" : undefined}
      onBack={() => navigateToCatalogue(route.cataloguePath)}
    />
  ) : (
    <FilmCatalogue
      isArchived={isArchived}
      isLoggingOut={logoutMutation.isPending}
      onChangeCatalogue={() =>
        navigateToCatalogue(isArchived ? "/" : ARCHIVED_FILMS_PATH)
      }
      onLogout={() => logoutMutation.mutate()}
      onSelectFilm={navigateToFilm}
    />
  );
}
