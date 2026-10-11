import { ChevronRight } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type UserPath } from "../../api/client";
import mark from "../../assets/brand/eco-master-mark.webp";
import { Emoji } from "../../components/Emoji";
import { changeLanguage } from "../../i18n";
import { LANGUAGE_NAMES, LANGUAGES, pickLanguage, type Language } from "../../i18n/languages";
import { useUser } from "../../state/user";
import { haptic } from "../../telegram";

const PATHS: { value: UserPath; icon: string }[] = [
  { value: "student", icon: "🎒" },
  { value: "teacher", icon: "👩‍🏫" },
  { value: "general", icon: "🏡" },
];

/**
 * First screen: the language (already set from Telegram, so usually no tap needed) and who the
 * user is. One tap on a role saves both and moves on (TZ 8.1, shortened).
 */
export function WelcomeStep({ onDone }: { onDone: () => void }) {
  const { t, i18n } = useTranslation();
  const { user, setUser } = useUser();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const selected = pickLanguage(i18n.language);

  async function selectLanguage(language: Language) {
    haptic.tap();
    await changeLanguage(language);
  }

  async function choose(path: UserPath) {
    if (busy) return;
    haptic.tap();
    setBusy(true);
    setFailed(false);
    try {
      await api.onboardingLanguage(selected);
      setUser(await api.onboardingPath(path));
      onDone();
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="stack stack--lg welcome">
      <div className="segmented segmented--small" role="radiogroup" aria-label={t("onboarding.language.title")}>
        {LANGUAGES.map((language) => (
          <button
            key={language}
            type="button"
            role="radio"
            aria-checked={selected === language}
            className={selected === language ? "segmented__item is-active" : "segmented__item"}
            onClick={() => void selectLanguage(language)}
          >
            {LANGUAGE_NAMES[language]}
          </button>
        ))}
      </div>

      <div className="welcome__hero">
        <img className="brand-mark" src={mark} alt="Eco-Master" />
        <h1>{t("onboarding.headline")}</h1>
      </div>

      <div className="stack">
        <h2>{t("onboarding.path.title")}</h2>
        {PATHS.map(({ value, icon }) => (
          <button
            key={value}
            type="button"
            className={user.path === value ? "choice is-selected" : "choice"}
            disabled={busy}
            onClick={() => void choose(value)}
          >
            <span className="choice__icon" aria-hidden="true">
              <Emoji char={icon} />
            </span>
            <span className="choice__body">
              <span className="choice__title">{t(`onboarding.path.${value}`)}</span>
              <span className="hint small">{t(`onboarding.path.${value}Hint`)}</span>
            </span>
            <ChevronRight size={20} aria-hidden="true" />
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
