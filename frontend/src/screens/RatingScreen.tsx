import { ChevronRight, Flag, Trophy } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api, type LeaderboardEntry } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { Emoji } from "../components/Emoji";
import { Avatar, LEVEL_EMOJI, TopBar } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { haptic } from "../telegram";
import { BoardRow } from "./classes/parts";

type Tab = "league" | "class" | "all";
const TABS: Tab[] = ["league", "class", "all"];
const TIER_EMOJI = ["🥉", "🥈", "🥇", "💎"];

/** Rating: the weekly league group, the class board and the all-time board. */
export function RatingScreen() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("league");
  return (
    <main className="screen screen--with-nav">
      <TopBar />
      <h1 className="row">
        <Trophy size={24} aria-hidden="true" /> {t("rating.title")}
      </h1>
      <div className="tabs tabs--three section" role="tablist">
        {TABS.map((value) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={tab === value}
            className={tab === value ? "tabs__item is-active" : "tabs__item"}
            onClick={() => {
              haptic.tap();
              setTab(value);
            }}
          >
            {t(`rating.tabs.${value}`)}
          </button>
        ))}
      </div>
      {tab === "league" && <LeagueView />}
      {tab === "class" && <ClassView />}
      {tab === "all" && <AllTimeView />}
    </main>
  );
}

/** The user's group of this week: who goes up, who goes down. */
function LeagueView() {
  const { t } = useTranslation();
  const data = useLoad(() => api.league(), []);
  const league = data.data;
  if (data.loading && !league) return <InlineLoading />;
  if (data.error !== undefined && !league) return <InlineError error={data.error} onRetry={data.reload} />;
  if (!league) return null;

  const size = league.entries.length;
  const tierName = (tier: number) => t(`league.tier${tier}`);
  const last = league.last_week;
  const marker = (rank: number) =>
    rank <= league.promote ? "up" : rank > size - league.demote ? "down" : undefined;

  return (
    <div className="stack section">
      <section className={`card league-head league-head--${league.tier}`}>
        <span className="league-head__badge" aria-hidden="true">
          <Emoji char={TIER_EMOJI[league.tier]} />
        </span>
        <span className="list-row__text">
          <strong>{tierName(league.tier)}</strong>
          <span className="hint small">{t("league.daysLeft", { count: league.days_left })}</span>
        </span>
      </section>

      {last && last.tier_after > last.tier_before && (
        <p className="note note--ok">
          <Emoji char="🎉" /> {t("league.promoted", { tier: tierName(last.tier_after) })}
        </p>
      )}
      {last && last.tier_after < last.tier_before && (
        <p className="note">
          <Emoji char="💪" /> {t("league.demoted", { tier: tierName(last.tier_after) })}
        </p>
      )}

      {!league.joined ? (
        <section className="empty-state">
          <Emoji char="🌱" className="empty-state__icon" />
          <p className="text-2">{t("league.notJoined")}</p>
          <Link className="btn" to="/games">
            {t("games.play")}
          </Link>
        </section>
      ) : (
        <>
          <ol className="list">
            {league.entries.map((entry) => (
              <li key={entry.user_id}>
                <BoardRow member={entry} marker={marker(entry.rank)} />
              </li>
            ))}
          </ol>
          {league.promote > 0 && <p className="hint small">{t("league.rules", { count: league.promote })}</p>}
        </>
      )}
    </div>
  );
}

/** The pupil's class board of this week, or how to get into a class. */
function ClassView() {
  const { t } = useTranslation();
  const data = useLoad(() => api.myClass(), []);
  if (data.loading && data.data === undefined) return <InlineLoading />;
  if (data.error !== undefined && data.data === undefined) return <InlineError error={data.error} onRetry={data.reload} />;
  const mine = data.data;
  if (!mine) {
    return (
      <section className="empty-state section">
        <Emoji char="🏫" className="empty-state__icon" />
        <p className="text-2">{t("classes.none")}</p>
      </section>
    );
  }
  return (
    <div className="stack section">
      <Link className="list-row" to="/my-class">
        <span className="icon-tile icon-tile--sky" aria-hidden="true">
          <Emoji char="🏫" />
        </span>
        <span className="list-row__text">
          <strong>{mine.name}</strong>
          <span className="hint small">{t("classes.open")}</span>
        </span>
        <ChevronRight className="list-row__chevron" size={20} />
      </Link>
      <ol className="list">
        {mine.members.map((member) => (
          <li key={member.user_id}>
            <BoardRow member={member} />
          </li>
        ))}
      </ol>
    </div>
  );
}

/** All-time board (TZ 8.7): the top 100 and the user's own place. */
function AllTimeView() {
  const { t } = useTranslation();
  const board = useLoad(() => api.leaderboard("all"), []);
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
    <>
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
    </>
  );
}

function PodiumPlace({ entry, onReport }: { entry: LeaderboardEntry; onReport: () => void }) {
  const { t } = useTranslation();
  const medal = ["🥇", "🥈", "🥉"][entry.rank - 1];
  return (
    <div className={`podium__place podium__place--${entry.rank}`}>
      <Avatar id={entry.user_id} emoji={entry.avatar} size={entry.rank === 1 ? "xl" : "lg"} />
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
      <Avatar id={entry.user_id} emoji={entry.avatar} />
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
