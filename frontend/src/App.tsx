import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { logout } from "./api/auth";
import { AuthScreen, type AuthMode } from "./components/AuthScreen";
import { FilmCatalogue } from "./components/FilmCatalogue";
import { FilmDetail } from "./components/FilmDetail";
import { useAuthStore } from "./store/auth";
import { useCatalogueStore } from "./store/catalogue";

const ARCHIVED_FILMS_PATH = "/films/archives/";
const FILMS_PATH = "/films/";
const LOGIN_PATH = "/login/";

type CataloguePath = typeof FILMS_PATH | typeof ARCHIVED_FILMS_PATH;

interface AppRoute {
  authMode: AuthMode;
  cataloguePath: CataloguePath;
  filmId: number | null;
  isAuthRoute: boolean;
}

function isCataloguePath(value: unknown): value is CataloguePath {
  return value === FILMS_PATH || value === ARCHIVED_FILMS_PATH;
}

function routeFromLocation(): AppRoute {
  const pathname = location.pathname;
  const match = pathname.match(/^\/films\/(\d+)\/?$/);
  if (match) {
    const cataloguePath = (history.state as { cataloguePath?: unknown } | null)
      ?.cataloguePath;
    return {
      authMode: "register",
      cataloguePath: isCataloguePath(cataloguePath)
        ? cataloguePath
        : FILMS_PATH,
      filmId: Number(match[1]),
      isAuthRoute: false,
    };
  }
  return {
    authMode:
      pathname === LOGIN_PATH || pathname === "/login" ? "login" : "register",
    cataloguePath:
      pathname === ARCHIVED_FILMS_PATH ? ARCHIVED_FILMS_PATH : FILMS_PATH,
    filmId: null,
    isAuthRoute: pathname !== FILMS_PATH && pathname !== ARCHIVED_FILMS_PATH,
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
    setRoute({ ...route, filmId: selectedFilmId, isAuthRoute: false });
  };

  const navigateToCatalogue = (cataloguePath: CataloguePath) => {
    history.pushState(null, "", cataloguePath);
    useCatalogueStore.getState().setPage(1);
    setRoute({
      authMode: "register",
      cataloguePath,
      filmId: null,
      isAuthRoute: false,
    });
  };

  const navigateToAuth = (authMode: AuthMode) => {
    history.pushState(null, "", authMode === "login" ? LOGIN_PATH : "/");
    setRoute({
      authMode,
      cataloguePath: FILMS_PATH,
      filmId: null,
      isAuthRoute: true,
    });
  };

  if (!isAuthenticated && route.isAuthRoute) {
    return (
      <AuthScreen
        mode={route.authMode}
        onBrowse={() => navigateToCatalogue(FILMS_PATH)}
        onLogin={() => navigateToCatalogue(FILMS_PATH)}
        onModeChange={navigateToAuth}
      />
    );
  }

  const isArchived = route.cataloguePath === ARCHIVED_FILMS_PATH;

  return route.filmId !== null ? (
    <FilmDetail
      filmId={route.filmId}
      backLabel={isArchived ? "Retour aux films archivés" : undefined}
      isAuthenticated={isAuthenticated}
      onBack={() => navigateToCatalogue(route.cataloguePath)}
    />
  ) : (
    <FilmCatalogue
      isArchived={isArchived}
      isAuthenticated={isAuthenticated}
      isLoggingOut={logoutMutation.isPending}
      onChangeCatalogue={() =>
        navigateToCatalogue(isArchived ? FILMS_PATH : ARCHIVED_FILMS_PATH)
      }
      onLogin={() => navigateToAuth("login")}
      onLogout={() => {
        navigateToAuth("login");
        logoutMutation.mutate();
      }}
      onSelectFilm={navigateToFilm}
    />
  );
}
