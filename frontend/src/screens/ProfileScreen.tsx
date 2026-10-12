import { Camera, Hammer, ListChecks, Pencil, Settings } from "lucide-react";
import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../api/client";
import { BadgeGrid } from "../components/BadgeGrid";
import { InlineError, InlineLoading } from "../components/common";
import { Emoji } from "../components/Emoji";
import { ShareButton } from "../components/ShareButton";
import { Tree } from "../components/Tree";
import { treeGrowth } from "../components/treeDrawing";
import { Avatar, avatarEmoji, LEVEL_EMOJI, levelProgress, ProgressBar, TopBar } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { useUser } from "../state/user";
import { canShareStory, haptic, shareStory } from "../telegram";

/** The user's progress: avatar, the tree, numbers and badges. Settings are behind the gear. */
export function ProfileScreen() {
  const { t } = useTranslation();
  const { user } = useUser();
  const stats = useLoad(() => api.myStats(), [user.points_total]);
  const badges = useLoad(() => api.myBadges(), [user.points_total]);
  const [choosing, setChoosing] = useState(false);

  const s = stats.data;
  const earned = badges.data?.filter((b) => b.earned_at).length ?? 0;

  return (
    <main className="screen screen--with-nav">
      <TopBar />

      <section className="card profile-head">
        <button
          type="button"
          className="avatar-button"
          onClick={() => setChoosing(true)}
          aria-label={t("profile.avatarTitle")}
        >
          <Avatar id={user.id} emoji={user.avatar} size="lg" />
          <span className="avatar-button__edit" aria-hidden="true">
            <Pencil size={13} />
          </span>
        </button>
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

      <TreeCard />

      {stats.error !== undefined && !s && <InlineError error={stats.error} onRetry={stats.reload} />}
      {s && (
        <div className="stat-row">
          <Stat icon={<Emoji char="🔥" />} value={String(s.streak_current)} label={t("profile.streak")} />
          <Stat icon={<ListChecks size={20} />} value={String(s.tasks_done)} label={t("profile.tasks")} />
          <Stat icon={<Hammer size={20} />} value={`${s.projects_done}/${s.projects_total}`} label={t("profile.projects")} />
          <Stat icon={<Emoji char="♻️" />} value={String(s.sorted_correct)} label={t("profile.sorted")} />
        </div>
      )}

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

      {choosing && <AvatarSheet onClose={() => setChoosing(false)} />}
    </main>
  );
}

/** "My tree": it grows with the points; apples come after the top level. Shared to Stories. */
function TreeCard() {
  const { t } = useTranslation();
  const { user } = useUser();
  const level = levelProgress(user);
  const levelName = t(`levels.${level.code}`);
  const { fruits } = treeGrowth(user.points_total);
  return (
    <section className="card tree-card">
      <h2 className="tree-card__title">{t("tree.title")}</h2>
      <div className="tree-card__sky">
        <Tree points={user.points_total} size={184} label={t("tree.label", { level: levelName })} />
      </div>
      {level.next && level.nextCode ? (
        <div className="tree-card__next">
          <ProgressBar value={level.percent} max={100} />
          <span className="tree-card__goal" aria-label={t("tree.toNext", { count: level.next - user.points_total })}>
            <Emoji char="⭐" /> {level.next - user.points_total} → <Emoji char={LEVEL_EMOJI[level.nextCode]} />
          </span>
        </div>
      ) : (
        <span className="chip tree-card__fruits" aria-label={t("tree.fruits", { count: fruits })}>
          <Emoji char="🍎" /> {fruits}
        </span>
      )}
      <div className="tree-card__actions">
        {canShareStory() && <StoryButton />}
        <ShareButton kind="progress" label={t("share.progress")} className="btn btn--soft btn--block" />
      </div>
    </section>
  );
}

function StoryButton() {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function share() {
    haptic.tap();
    setBusy(true);
    setFailed(false);
    try {
      const story = await api.shareStory();
      shareStory(story.media_url, story.text);
    } catch {
      haptic.error();
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className="btn btn--block" disabled={busy} onClick={() => void share()}>
        <Camera size={18} aria-hidden="true" /> {t("share.story")}
      </button>
      {failed && (
        <p className="error-text small" role="alert">
          {t("share.error")}
        </p>
      )}
    </>
  );
}

/** All animals; locked ones show the level that opens them. */
function AvatarSheet({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const { user, setUser } = useUser();
  const avatars = useLoad(() => api.myAvatars(), []);
  const [saving, setSaving] = useState(false);
  const [failed, setFailed] = useState(false);
  const [hint, setHint] = useState<string | null>(null);
  const current = avatarEmoji(user.id, user.avatar);

  async function choose(emoji: string) {
    haptic.tap();
    setSaving(true);
    setFailed(false);
    try {
      setUser(await api.setAvatar(emoji));
      haptic.success();
      onClose();
    } catch {
      haptic.error();
      setFailed(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label={t("profile.avatarTitle")} onClick={onClose}>
      <div className="sheet stack" onClick={(e) => e.stopPropagation()}>
        <h2>{t("profile.avatarTitle")}</h2>
        {avatars.loading && !avatars.data && <InlineLoading />}
        {avatars.error !== undefined && !avatars.data && <InlineError error={avatars.error} onRetry={avatars.reload} />}
        {avatars.data && (
          <ul className="avatar-grid">
            {avatars.data.map((avatar) => {
              const level = t(`levels.${avatar.level_code}`);
              const chosen = avatar.emoji === current;
              return (
                <li key={avatar.emoji}>
                  <button
                    type="button"
                    className={`avatar-grid__item${chosen ? " is-chosen" : ""}${avatar.unlocked ? "" : " is-locked"}`}
                    disabled={saving}
                    aria-pressed={chosen}
                    aria-label={avatar.unlocked ? undefined : t("profile.avatarLocked", { level })}
                    onClick={() => {
                      if (avatar.unlocked) void choose(avatar.emoji);
                      else setHint(t("profile.avatarLocked", { level }));
                    }}
                  >
                    <Emoji char={avatar.emoji} />
                    {!avatar.unlocked && (
                      <span className="avatar-grid__level" aria-hidden="true">
                        <Emoji char={LEVEL_EMOJI[avatar.level_code]} />
                      </span>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
        {hint && <p className="hint small strong">{hint}</p>}
        {failed && (
          <p className="error-text small" role="alert">
            {t("errors.unknown")}
          </p>
        )}
        <button type="button" className="link-button" onClick={onClose}>
          {t("common.cancel")}
        </button>
      </div>
    </div>
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
