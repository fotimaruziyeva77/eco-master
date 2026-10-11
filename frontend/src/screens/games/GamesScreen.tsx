import { Zap } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { ProgressBar, Toggle, TopBar } from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";

export function GamesScreen() {
  const { t } = useTranslation();
  const data = useLoad(() => api.games(), []);
  const [quick, setQuick] = useState(false);
  const games = data.data;

  return (
    <main className="screen screen--with-nav">
      <TopBar subtitle={t("nav.games")} />
      <h1>{t("games.title")}</h1>
      {data.loading && !games && <InlineLoading />}
      {data.error !== undefined && !games && <InlineError error={data.error} onRetry={data.reload} />}

      {games && (
        <div className="stack stack--lg section">
          <section className="card stack">
            <div className="row">
              <span className="icon-tile icon-tile--amber" aria-hidden="true">
                <Emoji char="🧠" />
              </span>
              <div className="list-row__text">
                <h2>{t("games.quizTitle")}</h2>
                <span className="hint small">{t("games.quizText", { count: games.quiz_total })}</span>
              </div>
            </div>
            <div className="row row--wrap">
              <span className="chip chip--sm chip--amber">{t("games.quizPoints")}</span>
              <span className="chip chip--sm chip--sky">{t("home.quizChip")}</span>
            </div>
            {games.quiz_total > 0 ? (
              <Link className="btn btn--block" to="/games/quiz">
                {t("games.play")}
              </Link>
            ) : (
              <p className="hint">{t("games.empty")}</p>
            )}
          </section>

          <section className="card stack">
            <div className="row">
              <span className="icon-tile icon-tile--sky" aria-hidden="true">
                <Emoji char="♻️" />
              </span>
              <div className="list-row__text">
                <h2>{t("games.sortTitle")}</h2>
                <span className="hint small">{t("games.sortText")}</span>
              </div>
            </div>
            <div className="row row--between small strong">
              <span>{t("games.dailyLimit", { points: games.game_points_today, cap: games.game_daily_cap })}</span>
              <span className="ok-text">{t("home.sortChip")}</span>
            </div>
            <ProgressBar value={games.game_points_today} max={games.game_daily_cap} />
            {games.game_item_count > 0 ? (
              <>
                <div className="row row--between">
                  <span className="row">
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
        </div>
      )}
    </main>
  );
}
