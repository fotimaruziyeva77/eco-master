import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { useLoad } from "../../hooks/useLoad";

export function GamesScreen() {
  const { t } = useTranslation();
  const data = useLoad(() => api.games(), []);
  const [quick, setQuick] = useState(false);
  const games = data.data;

  return (
    <main className="screen screen--with-nav">
      <h1>{t("games.title")}</h1>
      {data.loading && !games && <InlineLoading />}
      {data.error !== undefined && !games && <InlineError error={data.error} onRetry={data.reload} />}

      {games && (
        <>
          <section className="card game-card">
            <div className="game-card__icon" aria-hidden="true">
              ❓
            </div>
            <h2>{t("games.quizTitle")}</h2>
            <p className="hint">{t("games.quizText", { count: games.quiz_total })}</p>
            {games.quiz_total > 0 ? (
              <Link className="button button--block" to="/games/quiz">
                {t("games.play")}
              </Link>
            ) : (
              <p className="hint">{t("games.empty")}</p>
            )}
          </section>

          <section className="card game-card">
            <div className="game-card__icon" aria-hidden="true">
              🗑️
            </div>
            <h2>{t("games.sortTitle")}</h2>
            <p className="hint">{t("games.sortText")}</p>
            <p className="badge">
              {t("games.todayPoints", { points: games.game_points_today, cap: games.game_daily_cap })}
            </p>
            {games.game_item_count > 0 ? (
              <>
                <label className="switch">
                  <input type="checkbox" checked={quick} onChange={(e) => setQuick(e.target.checked)} />
                  <span>{t("games.quickMode")}</span>
                </label>
                <Link className="button button--block" to={quick ? "/games/sort?quick=1" : "/games/sort"}>
                  {t("games.play")}
                </Link>
              </>
            ) : (
              <p className="hint">{t("games.empty")}</p>
            )}
          </section>
        </>
      )}
    </main>
  );
}
