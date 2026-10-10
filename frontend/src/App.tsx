import { useCallback, useEffect, useState } from "react";

import { ApiError, fetchDevInitData, loginWithTelegram, type User } from "./api/client";
import { AppShell } from "./AppShell";
import i18n from "./i18n";
import { pickLanguage } from "./i18n/languages";
import { ErrorScreen } from "./screens/ErrorScreen";
import { LoadingScreen } from "./screens/LoadingScreen";
import { OnboardingFlow } from "./screens/onboarding/OnboardingFlow";
import { OpenInTelegramScreen } from "./screens/OpenInTelegramScreen";
import { UserProvider } from "./state/user";
import { getInitData, setupTelegramUi } from "./telegram";

type State =
  | { kind: "loading" }
  | { kind: "outside" }
  | { kind: "error"; messageKey: string }
  | { kind: "ready" };

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
  const [state, setState] = useState<State>({ kind: "loading" });
  const [user, setUserState] = useState<User | null>(null);
  const setUser = useCallback((next: User) => setUserState(next), []);

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
      const loggedIn = await loginWithTelegram(initData);
      // During onboarding the language screen decides; afterwards the saved language wins.
      if (loggedIn.onboarding_step !== "language") await i18n.changeLanguage(loggedIn.language);
      setUserState(loggedIn);
      setState({ kind: "ready" });
    } catch (error) {
      setState({ kind: "error", messageKey: errorKey(error) });
    }
    // Must not depend on the translation hook: changing language would log in again.
  }, []);

  useEffect(() => {
    setupTelegramUi();
    void start();
  }, [start]);

  if (state.kind === "loading") return <LoadingScreen />;
  if (state.kind === "outside") return <OpenInTelegramScreen />;
  if (state.kind === "error" || !user) {
    return <ErrorScreen messageKey={state.kind === "error" ? state.messageKey : "errors.unknown"} onRetry={start} />;
  }

  return (
    <UserProvider user={user} setUser={setUser}>
      {user.onboarding_step === "done" ? <AppShell /> : <OnboardingFlow />}
    </UserProvider>
  );
}
