import { Flag, Trophy } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type LeaderboardEntry, type Period } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { Emoji } from "../components/Emoji";
import { Avatar, LEVEL_EMOJI, TopBar } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { haptic } from "../telegram";

/** Leaderboard (TZ 8.7): weekly and all-time, top 100 plus the user's own place. */
export function RatingScreen() {
  const { t } = useTranslation();
  const [period, setPeriod] = useState<Period>("week");
  const board = useLoad(() => api.leaderboard(period), [period]);
  const [reporting, setReporting] = useState<LeaderboardEntry | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const entries = board.data?.entries ?? [];
  const me = board.data?.me ?? null;
  const podium = entries.slice(0, 3);
  const rest = entries.slice(3);
  const meInList = entries.some((e) => e.is_me);

  async function sendReport(entry: LeaderboardEntry) {
    setReporting(null);
    try {
      await api.report(entry.user_id);
      haptic.success();
      setNotice(t("rating.reported"));
    } catch {
      setNotice(t("errors.unknown"));
    }
  }

  return (
    <main className="screen screen--with-nav">
      <TopBar />
      <div className="section-head">
        <h1 className="row">
          <Trophy size={24} aria-hidden="true" /> {t("rating.title")}
        </h1>
      </div>
      <div className="tabs" role="tablist">
        {(["week", "all"] as const).map((p) => (
          <button
            key={p}
            type="button"
            role="tab"
            aria-selected={period === p}
            className={period === p ? "tabs__item is-active" : "tabs__item"}
            onClick={() => setPeriod(p)}
          >
            {t(`rating.${p}`)}
          </button>
        ))}
      </div>
      {notice && (
        <p className="toast" role="status" style={{ marginTop: 12 }}>
          {notice}
        </p>
      )}

      {board.loading && !board.data && <InlineLoading />}
      {board.error !== undefined && !board.data && <InlineError error={board.error} onRetry={board.reload} />}
      {board.data && entries.length === 0 && <p className="empty">{t("rating.empty")}</p>}

      {podium.length > 0 && (
        <section className="card" style={{ marginTop: 16, paddingBottom: 0 }}>
          <div className="podium">
            {[podium[1], podium[0], podium[2]].map((entry, i) =>
              entry ? (
                <PodiumPlace key={entry.user_id} entry={entry} onReport={() => setReporting(entry)} />
              ) : (
                <span key={`empty-${i}`} />
              ),
            )}
          </div>
        </section>
      )}

      {rest.length > 0 && (
        <ol className="list" style={{ marginTop: 12 }}>
          {rest.map((entry) => (
            <li key={entry.user_id}>
              <RankRow entry={entry} onReport={() => setReporting(entry)} />
            </li>
          ))}
        </ol>
      )}

      {board.data && !meInList && (
        <div className="me-sticky rank-row is-me">
          {me ? (
            <RankRowContent entry={me} />
          ) : (
            <span className="text-2">{t("rating.notRanked")}</span>
          )}
        </div>
      )}

      {reporting && (
        <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="report-title">
          <div className="sheet sheet--center stack">
            <span className="big-emoji" aria-hidden="true">
              <Emoji char="🚩" />
            </span>
            <h2 id="report-title">{t("rating.reportTitle", { name: reporting.nickname })}</h2>
            <p className="hint">{t("rating.reportText")}</p>
            <button type="button" className="btn btn--block" onClick={() => void sendReport(reporting)}>
              {t("rating.reportSend")}
            </button>
            <button type="button" className="link-button" onClick={() => setReporting(null)}>
              {t("common.cancel")}
            </button>
          </div>
        </div>
      )}
    </main>
  );
}

function PodiumPlace({ entry, onReport }: { entry: LeaderboardEntry; onReport: () => void }) {
  const { t } = useTranslation();
  const medal = ["🥇", "🥈", "🥉"][entry.rank - 1];
  return (
    <div className={`podium__place podium__place--${entry.rank}`}>
      <Avatar id={entry.user_id} size={entry.rank === 1 ? "xl" : "lg"} />
      <strong>{entry.is_me ? t("rating.you") : `@${entry.nickname}`}</strong>
      <span className="podium__points">{t("home.points", { count: entry.points })}</span>
      <span className="hint small">
        <Emoji char={LEVEL_EMOJI[entry.level_code]} /> {t(`levels.${entry.level_code}`)}
      </span>
      {!entry.is_me && (
        <button type="button" className="link-button small" onClick={onReport} aria-label={t("rating.report")}>
          <Flag size={14} />
        </button>
      )}
      <div className="podium__base" aria-hidden="true">
        <Emoji char={medal} />
      </div>
    </div>
  );
}

function RankRowContent({ entry }: { entry: LeaderboardEntry }) {
  const { t } = useTranslation();
  return (
    <>
      <span className="rank-row__place">{entry.rank}</span>
      <Avatar id={entry.user_id} />
      <span className="rank-row__name">
        <strong>
          @{entry.nickname} {entry.is_me && <span className="chip chip--sm">{t("rating.you")}</span>}
        </strong>
        <span className="hint small">
          <Emoji char={LEVEL_EMOJI[entry.level_code]} /> {t(`levels.${entry.level_code}`)}
        </span>
      </span>
      <span className="rank-row__points">{t("home.points", { count: entry.points })}</span>
    </>
  );
}

function RankRow({ entry, onReport }: { entry: LeaderboardEntry; onReport: () => void }) {
  const { t } = useTranslation();
  return (
    <div className={entry.is_me ? "rank-row is-me" : "rank-row"}>
      <RankRowContent entry={entry} />
      {!entry.is_me && (
        <button type="button" className="icon-button" onClick={onReport} aria-label={t("rating.report")}>
          <Flag size={18} />
        </button>
      )}
    </div>
  );
}
