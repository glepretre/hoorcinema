import { useMutation } from "@tanstack/react-query";
import { Button, Typography } from "antd";

import { logout } from "./api/auth";
import { AuthScreen } from "./components/AuthScreen";
import { useAuthStore } from "./store/auth";

const { Paragraph, Title } = Typography;

export default function App() {
  const isAuthenticated = useAuthStore((state) => state.accessToken !== null);
  const logoutMutation = useMutation({ mutationFn: logout });

  if (!isAuthenticated) {
    return <AuthScreen />;
  }

  return (
    <main className="session-page">
      <section aria-labelledby="session-title">
        <Typography.Text className="eyebrow">HOORCINEMA</Typography.Text>
        <Title id="session-title">Votre séance peut commencer.</Title>
        <Paragraph className="session-copy">
          Vous êtes connecté. Le catalogue de films arrive à l’étape suivante.
        </Paragraph>
        <Button
          className="logout-button"
          type="primary"
          size="large"
          loading={logoutMutation.isPending}
          onClick={() => logoutMutation.mutate()}
        >
          Se déconnecter
        </Button>
      </section>
    </main>
  );
}
