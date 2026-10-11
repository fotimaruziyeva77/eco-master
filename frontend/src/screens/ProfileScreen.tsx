import { Hammer, ListChecks, Settings } from "lucide-react";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../api/client";
import { BadgeGrid } from "../components/BadgeGrid";
import { InlineError, InlineLoading } from "../components/common";
import { Emoji } from "../components/Emoji";
import { ShareButton } from "../components/ShareButton";
import { Avatar, LEVEL_EMOJI, TopBar } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { useUser } from "../state/user";

/** The user's progress: level, numbers and badges. Settings are behind the gear. */
export function ProfileScreen() {
  const { t } = useTranslation();
  const { user } = useUser();
  const stats = useLoad(() => api.myStats(), [user.points_total]);
  const badges = useLoad(() => api.myBadges(), [user.points_total]);

  const s = stats.data;
  const earned = badges.data?.filter((b) => b.earned_at).length ?? 0;

  return (
    <main className="screen screen--with-nav">
      <TopBar />

      <section className="card profile-head">
        <Avatar id={user.id} size="lg" />
        <div className="stack" style={{ gap: 6, minWidth: 0 }}>
          <h2 className="profile-head__name">@{user.nickname}</h2>
          <span className="ok-text strong">
            <Emoji char={LEVEL_EMOJI[user.level.code]} /> {t(`levels.${user.level.code}`)}
          </span>
          <div className="row row--wrap">
            <span className="chip chip--amber chip--sm">
              <Emoji char="⭐" /> {user.points_total}
            </span>
            {s?.rank_all && (
              <span className="chip chip--sm">
                <Emoji char="🏆" /> {t("profile.rank", { rank: s.rank_all })}
              </span>
            )}
          </div>
        </div>
        <Link to="/settings" className="icon-button profile-head__gear" aria-label={t("profile.settings")}>
          <Settings size={20} />
        </Link>
      </section>

      {stats.error !== undefined && !s && <InlineError error={stats.error} onRetry={stats.reload} />}
      {s && (
        <div className="stat-row">
          <Stat icon={<Emoji char="🔥" />} value={String(s.streak_current)} label={t("profile.streak")} />
          <Stat icon={<ListChecks size={20} />} value={String(s.tasks_done)} label={t("profile.tasks")} />
          <Stat icon={<Hammer size={20} />} value={`${s.projects_done}/${s.projects_total}`} label={t("profile.projects")} />
          <Stat icon={<Emoji char="♻️" />} value={String(s.sorted_correct)} label={t("profile.sorted")} />
        </div>
      )}
      <div className="stack" style={{ marginTop: 12 }}>
        <ShareButton kind="progress" label={t("share.progress")} />
      </div>

      <section className="section">
        <div className="section-head">
          <h2>{t("badges.title")}</h2>
          {badges.data && (
            <span className="chip chip--sm">
              {earned} / {badges.data.length}
            </span>
          )}
        </div>
        {badges.loading && !badges.data && <InlineLoading />}
        {badges.data && <BadgeGrid badges={badges.data} />}
      </section>
    </main>
  );
}

function Stat({ icon, value, label }: { icon: ReactNode; value: string; label: string }) {
  return (
    <section className="stat-mini">
      <span className="stat-mini__icon" aria-hidden="true">
        {icon}
      </span>
      <strong>{value}</strong>
      <span>{label}</span>
    </section>
  );
}
