import { useMutation } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { logout } from "./api/auth";
import { AuthScreen } from "./components/AuthScreen";
import { FilmCatalogue } from "./components/FilmCatalogue";
import { FilmDetail } from "./components/FilmDetail";
import { useAuthStore } from "./store/auth";
import { useCatalogueStore } from "./store/catalogue";

function filmIdFromPath(pathname: string): number | null {
  const match = pathname.match(/^\/films\/(\d+)\/?$/);
  return match ? Number(match[1]) : null;
}

export default function App() {
  const isAuthenticated = useAuthStore((state) => state.accessToken !== null);
  const setSelectedFilmId = useCatalogueStore(
    (state) => state.setSelectedFilmId,
  );
  const [filmId, setFilmId] = useState(() => filmIdFromPath(location.pathname));
  const logoutMutation = useMutation({ mutationFn: logout });

  useEffect(() => {
    setSelectedFilmId(filmId);
  }, [filmId, setSelectedFilmId]);

  useEffect(() => {
    const handleNavigation = () => setFilmId(filmIdFromPath(location.pathname));
    window.addEventListener("popstate", handleNavigation);
    return () => window.removeEventListener("popstate", handleNavigation);
  }, []);

  const navigateToFilm = (selectedFilmId: number) => {
    history.pushState(null, "", `/films/${selectedFilmId}/`);
    setFilmId(selectedFilmId);
  };

  const navigateToCatalogue = () => {
    history.pushState(null, "", "/");
    setFilmId(null);
  };

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  return filmId !== null ? (
    <FilmDetail filmId={filmId} onBack={navigateToCatalogue} />
  ) : (
    <FilmCatalogue
      isLoggingOut={logoutMutation.isPending}
      onLogout={() => logoutMutation.mutate()}
      onSelectFilm={navigateToFilm}
    />
  );
}
