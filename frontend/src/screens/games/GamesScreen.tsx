import { Zap } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { ProgressBar, Toggle, TopBar } from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";

/** The two games as big cards: picture, name, one line, play. */
export function GamesScreen() {
  const { t } = useTranslation();
  const data = useLoad(() => api.games(), []);
  const [quick, setQuick] = useState(false);
  const games = data.data;

  return (
    <main className="screen screen--with-nav">
      <TopBar />
      <h1>{t("games.title")}</h1>
      {data.loading && !games && <InlineLoading />}
      {data.error !== undefined && !games && <InlineError error={data.error} onRetry={data.reload} />}

      {games && (
        <div className="stack stack--lg section">
          <section className="card game-card game-card--sky stack">
            <div className="row">
              <span className="game-card__icon" aria-hidden="true">
                <Emoji char="♻️" />
              </span>
              <div className="list-row__text">
                <h2>{t("games.sortTitle")}</h2>
                <span className="text-2">{t("games.sortText")}</span>
              </div>
            </div>
            <div className="stack" style={{ gap: 6 }}>
              <span className="row row--between small strong">
                <span>{t("games.today")}</span>
                <span>
                  <Emoji char="⭐" /> {games.game_points_today} / {games.game_daily_cap}
                </span>
              </span>
              <ProgressBar value={games.game_points_today} max={games.game_daily_cap} thin />
            </div>
            {games.game_item_count > 0 ? (
              <>
                <div className="row row--between">
                  <span className="row strong">
                    <Zap size={18} aria-hidden="true" /> {t("games.quickMode")}
                  </span>
                  <Toggle checked={quick} onChange={setQuick} label={t("games.quickMode")} />
                </div>
                <Link className="btn btn--block" to={quick ? "/games/sort?quick=1" : "/games/sort"}>
                  {t("games.play")}
                </Link>
              </>
            ) : (
              <p className="hint">{t("games.empty")}</p>
            )}
          </section>

          <section className="card game-card game-card--amber stack">
            <div className="row">
              <span className="game-card__icon" aria-hidden="true">
                <Emoji char="🧠" />
              </span>
              <div className="list-row__text">
                <h2>{t("games.quizTitle")}</h2>
                <span className="text-2">{t("games.quizText", { count: games.quiz_total })}</span>
              </div>
            </div>
            {games.quiz_total > 0 ? (
              <Link className="btn btn--block" to="/games/quiz">
                {t("games.play")}
              </Link>
            ) : (
              <p className="hint">{t("games.empty")}</p>
            )}
          </section>
        </div>
      )}
    </main>
  );
}
