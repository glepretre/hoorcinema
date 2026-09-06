import { useMutation } from "@tanstack/react-query";

import { logout } from "./api/auth";
import { AuthScreen } from "./components/AuthScreen";
import { FilmCatalogue } from "./components/FilmCatalogue";
import { useAuthStore } from "./store/auth";

export default function App() {
  const isAuthenticated = useAuthStore((state) => state.accessToken !== null);
  const logoutMutation = useMutation({ mutationFn: logout });

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  return (
    <FilmCatalogue
      isLoggingOut={logoutMutation.isPending}
      onLogout={() => logoutMutation.mutate()}
    />
  );
}
