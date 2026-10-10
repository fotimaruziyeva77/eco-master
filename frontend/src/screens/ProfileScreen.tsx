import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../api/client";
import { BadgeGrid } from "../components/BadgeGrid";
import { LevelProgress } from "../components/LevelProgress";
import { LANGUAGE_NAMES, LANGUAGES, type Language } from "../i18n/languages";
import { useUser } from "../state/user";

/** Profile with level and badges; statistics and settings are completed in phase 4. */
export function ProfileScreen() {
  const { t, i18n } = useTranslation();
  const { user, setUser } = useUser();
  const [saving, setSaving] = useState(false);

  async function changeLanguage(language: Language) {
    if (language === user.language || saving) return;
    setSaving(true);
    try {
      await i18n.changeLanguage(language);
      setUser(await api.updateMe({ language }));
    } catch {
      await i18n.changeLanguage(user.language);
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="screen screen--with-nav">
      <h1>
        <span aria-hidden="true">👤</span> {user.nickname}
      </h1>
      <section className="card">
        <LevelProgress user={user} />
      </section>

      <section className="card">
        <h2>{t("badges.title")}</h2>
        <BadgeGrid />
      </section>

      <section className="card">
        <h2 id="language-label">{t("profile.language")}</h2>
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

      <ul className="list">
        <li>
          <Link className="list-row" to="/privacy">
            <span className="list-row__icon list-row__icon--soft" aria-hidden="true">
              🔒
            </span>
            <span className="list-row__text">
              <strong>{t("profile.privacy")}</strong>
            </span>
            <span className="list-row__chevron" aria-hidden="true">
              ›
            </span>
          </Link>
        </li>
      </ul>
    </main>
  );
}
