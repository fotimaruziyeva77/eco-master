import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { LevelProgress } from "../components/LevelProgress";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";
import { useUser } from "../state/user";

export function HomeScreen() {
  const { t } = useTranslation();
  const tr = useTr();
  const { user, setUser } = useUser();
  const home = useLoad(() => api.home(), []);

  // The home payload carries fresh points; keep the shared user in sync.
  useEffect(() => {
    if (home.data) setUser(home.data.user);
  }, [home.data, setUser]);

  return (
    <main className="screen screen--with-nav">
      <header className="home-header">
        <h1>{t("home.greeting", { name: user.nickname })}</h1>
        {user.streak_current > 0 && (
          <span className="badge">{t("home.streak", { count: user.streak_current })}</span>
        )}
      </header>

      <section className="card">
        <LevelProgress user={user} />
      </section>

      {home.loading && !home.data && <InlineLoading />}
      {home.error !== undefined && !home.data && <InlineError error={home.error} onRetry={home.reload} />}

      {home.data?.tip && (
        <section className="card card--tip">
          <h2>{t("home.tipTitle")}</h2>
          <p>{tr(home.data.tip.text)}</p>
        </section>
      )}

      <section className="quick-actions">
        <Link className="tile" to="/games">
          <span className="tile__icon" aria-hidden="true">
            ❓
          </span>
          <span>{t("home.quiz")}</span>
        </Link>
        <Link className="tile" to="/games">
          <span className="tile__icon" aria-hidden="true">
            🗑️
          </span>
          <span>{t("home.game")}</span>
        </Link>
      </section>

      {home.data && (
        <section>
          <h2 className="section-title">{t("home.wasteTypes")}</h2>
          <div className="tiles">
            {home.data.categories.map((category) => (
              <Link
                key={category.code}
                className="tile"
                to={`/learn/${category.code}`}
                style={{ borderColor: category.color }}
              >
                <span className="tile__icon" aria-hidden="true">
                  {category.icon}
                </span>
                <span>{tr(category.name)}</span>
              </Link>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
