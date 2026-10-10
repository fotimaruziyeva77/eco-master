import { useState } from "react";
import { useTranslation } from "react-i18next";

import { updateMe, type User } from "../api/client";
import { LANGUAGE_NAMES, LANGUAGES, type Language } from "../i18n/languages";

type Props = { user: User; onUserChange: (user: User) => void };

/** Phase 1 placeholder: proves login, theming and language switching end to end. */
export function HomeScreen({ user, onUserChange }: Props) {
  const { t, i18n } = useTranslation();
  const [saving, setSaving] = useState(false);

  async function changeLanguage(language: Language) {
    if (language === user.language || saving) return;
    setSaving(true);
    try {
      await i18n.changeLanguage(language);
      onUserChange(await updateMe({ language }));
    } catch {
      await i18n.changeLanguage(user.language);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="screen">
      <header className="hero">
        <div className="emoji" aria-hidden="true">
          🌱
        </div>
        <h1>{t("home.welcome")}</h1>
        <p className="hint">{t("home.building")}</p>
        <p className="badge">{t("home.points", { count: user.points_total })}</p>
      </header>

      <section className="card" aria-labelledby="language-label">
        <h2 id="language-label">{t("home.language")}</h2>
        <div className="segmented" role="radiogroup" aria-labelledby="language-label">
          {LANGUAGES.map((language) => (
            <button
              key={language}
              type="button"
              role="radio"
              aria-checked={user.language === language}
              className={user.language === language ? "segmented__item is-active" : "segmented__item"}
              disabled={saving}
              onClick={() => void changeLanguage(language)}
            >
              {LANGUAGE_NAMES[language]}
            </button>
          ))}
        </div>
      </section>
    </main>
  );
}
