import { Check } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type UserPath } from "../../api/client";
import { useUser } from "../../state/user";
import { haptic } from "../../telegram";

const PATHS: { value: UserPath; icon: string; tone?: "amber" | "sky" }[] = [
  { value: "student", icon: "🎓" },
  { value: "teacher", icon: "👩‍🏫", tone: "sky" },
  { value: "general", icon: "🏡", tone: "amber" },
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
    <section className="stack stack--lg">
      <div className="stack">
        <h1>{t("onboarding.path.title")}</h1>
        <p className="hint">{t("onboarding.path.subtitle")}</p>
      </div>
      <div className="stack">
        {PATHS.map(({ value, icon, tone }) => (
          <button
            key={value}
            type="button"
            className={user.path === value ? "choice is-selected" : "choice"}
            disabled={busy}
            onClick={() => void choose(value)}
          >
            <span className="choice__icon" aria-hidden="true">
              {icon}
            </span>
            <span className="choice__body">
              <span className="row row--wrap">
                <span className="choice__title">{t(`roles.${value}`)}</span>
                <span className={tone ? `chip chip--sm chip--${tone}` : "chip chip--sm"}>
                  {t(`onboarding.path.${value}Tag`)}
                </span>
              </span>
              <span className="hint small">{t(`onboarding.path.${value}Hint`)}</span>
            </span>
            <span className="choice__check" aria-hidden="true">
              <Check size={16} />
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
