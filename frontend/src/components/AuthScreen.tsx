import { useMutation } from "@tanstack/react-query";
import { Alert, Button, Form, Input, Typography } from "antd";
import { useState } from "react";

import {
  type LoginData,
  type RegistrationData,
  login,
  registerSpectator,
} from "../api/auth";
import { ApiError } from "../api/client";

const { Paragraph, Text, Title } = Typography;

type AuthMode = "register" | "login";

function errorMessage(error: Error): string {
  if (error instanceof ApiError && error.status === 401) {
    return "Identifiant ou mot de passe incorrect.";
  }
  if (error instanceof ApiError && error.status === 400) {
    return "Certains champs sont invalides. Vérifiez les informations saisies.";
  }
  return "Impossible de contacter le service. Réessayez dans un instant.";
}

export function AuthScreen() {
  const [mode, setMode] = useState<AuthMode>("register");
  const [registered, setRegistered] = useState(false);
  const registerMutation = useMutation({ mutationFn: registerSpectator });
  const loginMutation = useMutation({ mutationFn: login });
  const isRegister = mode === "register";
  const activeMutation = isRegister ? registerMutation : loginMutation;

  function changeMode(nextMode: AuthMode) {
    setMode(nextMode);
    setRegistered(false);
    registerMutation.reset();
    loginMutation.reset();
  }

  async function submitRegistration(values: RegistrationData) {
    await registerMutation.mutateAsync(values);
    setRegistered(true);
    setMode("login");
  }

  return (
    <main className="auth-page">
      <section className="auth-story" aria-labelledby="brand-title">
        <Text className="eyebrow">VOTRE CINÉMATHÈQUE</Text>
        <Title id="brand-title">Hoorcinema</Title>
        <Paragraph className="story-copy">
          Retrouvez les films qui vous marquent. Notez-les, gardez vos favoris
          et composez une collection à votre image.
        </Paragraph>
        <div className="film-strip" aria-hidden="true">
          <span />
          <span />
          <span />
        </div>
      </section>

      <section className="auth-panel" aria-labelledby="auth-title">
        <div className="auth-card">
          <Text className="eyebrow">BIENVENUE</Text>
          <Title id="auth-title" level={2}>
            {isRegister ? "Créer un compte" : "Se connecter"}
          </Title>
          <Paragraph className="auth-intro">
            {isRegister
              ? "Inscrivez-vous pour noter vos découvertes et retrouver vos films favoris."
              : "Accédez à votre espace personnel et poursuivez votre sélection."}
          </Paragraph>

          {registered && (
            <Alert
              type="success"
              showIcon
              title="Votre compte a été créé. Vous pouvez maintenant vous connecter."
            />
          )}
          {activeMutation.isError && (
            <Alert
              type="error"
              showIcon
              title={errorMessage(activeMutation.error)}
            />
          )}

          {isRegister ? (
            <Form<RegistrationData>
              key="register"
              layout="vertical"
              requiredMark={false}
              onFinish={submitRegistration}
            >
              <div className="name-fields">
                <Form.Item label="Prénom" name="first_name">
                  <Input autoComplete="given-name" />
                </Form.Item>
                <Form.Item label="Nom" name="last_name">
                  <Input autoComplete="family-name" />
                </Form.Item>
              </div>
              <Form.Item
                label="Nom d’utilisateur"
                name="username"
                rules={[
                  {
                    required: true,
                    message: "Saisissez un nom d’utilisateur.",
                  },
                ]}
              >
                <Input autoComplete="username" />
              </Form.Item>
              <Form.Item
                label="Adresse e-mail"
                name="email"
                rules={[
                  {
                    type: "email",
                    message: "Saisissez une adresse e-mail valide.",
                  },
                ]}
              >
                <Input autoComplete="email" inputMode="email" />
              </Form.Item>
              <Form.Item
                label="Mot de passe"
                name="password"
                extra="Utilisez au moins 8 caractères."
                rules={[
                  { required: true, message: "Saisissez un mot de passe." },
                ]}
              >
                <Input.Password autoComplete="new-password" />
              </Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                block
                loading={registerMutation.isPending}
              >
                Créer mon compte
              </Button>
              <Paragraph className="auth-switch">
                Vous avez déjà un compte ?{" "}
                <Button type="link" onClick={() => changeMode("login")}>
                  Se connecter
                </Button>
              </Paragraph>
            </Form>
          ) : (
            <Form<LoginData>
              key="login"
              layout="vertical"
              requiredMark={false}
              onFinish={(values) => loginMutation.mutate(values)}
            >
              <Form.Item
                label="Nom d’utilisateur"
                name="username"
                rules={[
                  {
                    required: true,
                    message: "Saisissez votre nom d’utilisateur.",
                  },
                ]}
              >
                <Input autoComplete="username" />
              </Form.Item>
              <Form.Item
                label="Mot de passe"
                name="password"
                rules={[
                  { required: true, message: "Saisissez votre mot de passe." },
                ]}
              >
                <Input.Password autoComplete="current-password" />
              </Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                block
                loading={loginMutation.isPending}
              >
                Se connecter
              </Button>
              <Paragraph className="auth-switch">
                Pas encore de compte ?{" "}
                <Button type="link" onClick={() => changeMode("register")}>
                  S’inscrire
                </Button>
              </Paragraph>
            </Form>
          )}
        </div>
      </section>
    </main>
  );
}
