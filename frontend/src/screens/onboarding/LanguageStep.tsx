import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../../api/client";
import { LANGUAGE_NAMES, LANGUAGES, type Language } from "../../i18n/languages";
import { useUser } from "../../state/user";
import { haptic } from "../../telegram";

export function LanguageStep({ onDone }: { onDone: () => void }) {
  const { t, i18n } = useTranslation();
  const { setUser } = useUser();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function choose(language: Language) {
    if (busy) return;
    haptic.tap();
    setBusy(true);
    setFailed(false);
    try {
      await i18n.changeLanguage(language);
      setUser(await api.onboardingLanguage(language));
      onDone();
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h1>{t("onboarding.language.title")}</h1>
      <p className="hint">{t("onboarding.language.subtitle")}</p>
      <div className="options">
        {LANGUAGES.map((language) => (
          <button
            key={language}
            type="button"
            className={i18n.language === language ? "option is-selected" : "option"}
            disabled={busy}
            onClick={() => void choose(language)}
          >
            <span className="option__title">{LANGUAGE_NAMES[language]}</span>
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
