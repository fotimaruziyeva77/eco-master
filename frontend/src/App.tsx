import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, fetchDevInitData, loginWithTelegram, type User } from "./api/client";
import { pickLanguage } from "./i18n/languages";
import { ErrorScreen } from "./screens/ErrorScreen";
import { HomeScreen } from "./screens/HomeScreen";
import { LoadingScreen } from "./screens/LoadingScreen";
import { OpenInTelegramScreen } from "./screens/OpenInTelegramScreen";
import { getInitData, setupTelegramUi } from "./telegram";

type State =
  | { kind: "loading" }
  | { kind: "outside" }
  | { kind: "error"; messageKey: string }
  | { kind: "ready"; user: User };

const DEV_AUTH = import.meta.env.DEV && import.meta.env.VITE_DEV_AUTH === "true";

function errorKey(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return "errors.auth";
    if (error.status === 403) return "errors.blocked";
    return "errors.unknown";
  }
  return "errors.network";
}

export default function App() {
  const { i18n } = useTranslation();
  const [state, setState] = useState<State>({ kind: "loading" });

  const start = useCallback(async () => {
    setState({ kind: "loading" });
    try {
      let initData = getInitData();
      if (!initData && DEV_AUTH) {
        initData = await fetchDevInitData(pickLanguage(navigator.language));
      }
      if (!initData) {
        setState({ kind: "outside" });
        return;
      }
      const user = await loginWithTelegram(initData);
      await i18n.changeLanguage(user.language);
      setState({ kind: "ready", user });
    } catch (error) {
      setState({ kind: "error", messageKey: errorKey(error) });
    }
  }, [i18n]);

  useEffect(() => {
    setupTelegramUi();
    void start();
  }, [start]);

  switch (state.kind) {
    case "loading":
      return <LoadingScreen />;
    case "outside":
      return <OpenInTelegramScreen />;
    case "error":
      return <ErrorScreen messageKey={state.messageKey} onRetry={start} />;
    case "ready":
      return (
        <HomeScreen user={state.user} onUserChange={(user) => setState({ kind: "ready", user })} />
      );
  }
}
