import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type UserPath } from "../../api/client";
import { useUser } from "../../state/user";
import { haptic } from "../../telegram";

const PATHS: { value: UserPath; icon: string }[] = [
  { value: "student", icon: "🎒" },
  { value: "teacher", icon: "👩‍🏫" },
  { value: "general", icon: "👨‍👩‍👧" },
];

export function PathStep({ onDone }: { onDone: () => void }) {
  const { t } = useTranslation();
  const { user, setUser } = useUser();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function choose(path: UserPath) {
    if (busy) return;
    haptic.tap();
    setBusy(true);
    setFailed(false);
    try {
      setUser(await api.onboardingPath(path));
      onDone();
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h1>{t("onboarding.path.title")}</h1>
      <p className="hint">{t("onboarding.path.subtitle")}</p>
      <div className="options">
        {PATHS.map(({ value, icon }) => (
          <button
            key={value}
            type="button"
            className={user.path === value ? "option is-selected" : "option"}
            disabled={busy}
            onClick={() => void choose(value)}
          >
            <span className="option__icon" aria-hidden="true">
              {icon}
            </span>
            <span>
              <span className="option__title">{t(`onboarding.path.${value}`)}</span>
              <span className="option__hint">{t(`onboarding.path.${value}Hint`)}</span>
            </span>
          </button>
        ))}
      </div>
      {failed && (
        <p className="error-text" role="alert">
          {t("errors.network")}
        </p>
      )}
    </section>
  );
}
