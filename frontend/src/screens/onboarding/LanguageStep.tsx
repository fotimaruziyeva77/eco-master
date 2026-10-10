import { Languages, Leaf } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api } from "../../api/client";
import { LANGUAGE_NAMES, LANGUAGES, pickLanguage, type Language } from "../../i18n/languages";
import { useUser } from "../../state/user";
import { haptic } from "../../telegram";

export function LanguageStep({ onDone }: { onDone: () => void }) {
  const { t, i18n } = useTranslation();
  const { setUser } = useUser();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const selected = pickLanguage(i18n.language);

  async function select(language: Language) {
    haptic.tap();
    await i18n.changeLanguage(language);
  }

  async function next() {
    setBusy(true);
    setFailed(false);
    try {
      setUser(await api.onboardingLanguage(selected));
      onDone();
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="stack stack--lg" style={{ textAlign: "center" }}>
      <span className="chip welcome-chip">
        <Leaf size={14} /> {t("onboarding.welcome")}
      </span>
      <div className="intro__art" style={{ margin: "0 auto" }} aria-hidden="true">
        🌍
      </div>
      <div className="stack">
        <h1>{t("onboarding.headline")}</h1>
        <p className="hint">{t("onboarding.subheadline")}</p>
      </div>
      <div className="card stack" style={{ textAlign: "left" }}>
        <span className="row strong">
          <Languages size={18} /> {t("onboarding.language.title")}
        </span>
        <div className="segmented" role="radiogroup" aria-label={t("onboarding.language.title")}>
          {LANGUAGES.map((language) => (
            <button
              key={language}
              type="button"
              role="radio"
              aria-checked={selected === language}
              className={selected === language ? "segmented__item is-active" : "segmented__item"}
              onClick={() => void select(language)}
            >
              {LANGUAGE_NAMES[language]}
            </button>
          ))}
        </div>
        <span className="hint small">{t("onboarding.language.subtitle")}</span>
      </div>
      {failed && (
        <p className="error-text" role="alert">
          {t("errors.network")}
        </p>
      )}
      <button type="button" className="btn btn--block" disabled={busy} onClick={() => void next()}>
        {t("onboarding.nickname.submit")}
      </button>
    </section>
  );
}
