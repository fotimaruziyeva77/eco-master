import {
  AtSign,
  Bell,
  ChevronRight,
  GraduationCap,
  Hammer,
  Languages,
  ListChecks,
  MessageCircle,
  ShieldCheck,
  Trash2,
  Trophy,
  UserRound,
  type LucideIcon,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api, ApiError, type UserPath } from "../api/client";
import { BadgeGrid } from "../components/BadgeGrid";
import { InlineError, InlineLoading } from "../components/common";
import { ShareButton } from "../components/ShareButton";
import { Avatar, LEVEL_EMOJI, ProgressBar, Toggle, TopBar } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { LANGUAGE_NAMES, LANGUAGES, type Language } from "../i18n/languages";
import { useUser } from "../state/user";
import { botChatLink, haptic, openTelegramLink, requestWriteAccess } from "../telegram";
import { nicknameFormatError } from "./onboarding/nickname";

type Sheet = "nickname" | "path" | "language" | "delete" | null;
const PATHS: UserPath[] = ["student", "teacher", "general"];
// Reminder times offered in settings: 08:00–20:00, every hour (TZ 8.5).
const REMINDER_TIMES = Array.from({ length: 13 }, (_, i) => `${String(8 + i).padStart(2, "0")}:00`);

export function ProfileScreen() {
  const { t } = useTranslation();
  const { user } = useUser();
  const stats = useLoad(() => api.myStats(), [user.points_total]);
  const badges = useLoad(() => api.myBadges(), [user.points_total]);
  const [sheet, setSheet] = useState<Sheet>(null);

  const s = stats.data;
  const bot = botChatLink();
  const earned = badges.data?.filter((b) => b.earned_at).length ?? 0;
  const accuracy = s && s.sorted_total > 0 ? Math.round((s.sorted_correct / s.sorted_total) * 100) : null;

  return (
    <main className="screen screen--with-nav">
      <TopBar subtitle={t("nav.profile")} />

      <section className="card profile-head">
        <Avatar id={user.id} size="lg" />
        <div className="stack" style={{ gap: 6, minWidth: 0 }}>
          <div className="row row--wrap">
            <h2>@{user.nickname}</h2>
            {user.path && <span className="chip chip--sm">{t(`roles.${user.path}`)}</span>}
          </div>
          <span className="ok-text small">
            {LEVEL_EMOJI[user.level.code]} {t(`levels.${user.level.code}`)}
          </span>
          <div className="row row--wrap">
            <span className="chip chip--amber chip--sm">⭐ {t("home.points", { count: user.points_total })}</span>
            {s?.rank_all && <span className="chip chip--sm">🏆 {t("profile.rank", { rank: s.rank_all })}</span>}
          </div>
        </div>
      </section>

      {stats.error !== undefined && !s && <InlineError error={stats.error} onRetry={stats.reload} />}
      {s && (
        <div className="stat-grid" style={{ marginTop: 12 }}>
          <Stat icon="🔥" tone="amber" note={t("profile.best", { count: s.streak_best })} value={t("profile.days", { count: s.streak_current })} label={t("profile.streak")} />
          <Stat icon={<ListChecks size={20} />} value={String(s.tasks_done)} label={t("profile.tasks")} />
          <Stat icon={<Hammer size={20} />} note={`${s.projects_done}/${s.projects_total}`} value={String(s.projects_done)} label={t("profile.projects")} />
          <Stat
            icon="♻️"
            tone="sky"
            note={accuracy !== null ? t("profile.accuracy", { percent: accuracy }) : undefined}
            value={String(s.sorted_correct)}
            label={t("profile.sorted")}
          />
        </div>
      )}
      <div className="stack" style={{ marginTop: 12 }}>
        <ShareButton kind="progress" label={t("share.progress")} />
      </div>

      <section className="section">
        <div className="section-head">
          <h2 className="row">
            <Trophy size={20} aria-hidden="true" /> {t("badges.title")}
          </h2>
          {badges.data && (
            <span className="chip chip--sm">
              {earned} / {badges.data.length}
            </span>
          )}
        </div>
        {badges.data && <ProgressBar value={earned} max={badges.data.length} />}
        {badges.loading && !badges.data && <InlineLoading />}
        {badges.data && <BadgeGrid badges={badges.data} />}
      </section>

      <section className="section">
        <h2 style={{ marginBottom: 12 }}>{t("profile.settings")}</h2>
        <ul className="list card settings-list">
          <SettingRow icon={AtSign} title={t("profile.nickname")} value={`@${user.nickname}`} onClick={() => setSheet("nickname")} />
          <SettingRow icon={UserRound} title={t("profile.role")} value={user.path ? t(`roles.${user.path}`) : ""} onClick={() => setSheet("path")} />
          <SettingRow icon={Languages} title={t("profile.language")} value={LANGUAGE_NAMES[user.language]} onClick={() => setSheet("language")} />
          <li>
            <ReminderSetting />
          </li>
          <li>
            <Link className="list-row" to="/teachers">
              <span className="icon-tile" aria-hidden="true">
                <GraduationCap size={20} />
              </span>
              <span className="list-row__text">
                <strong>{t("profile.teachers")}</strong>
              </span>
              <ChevronRight className="list-row__chevron" size={20} />
            </Link>
          </li>
          {bot && (
            // Whatever users write to the bot reaches the team (TZ 8.11).
            <SettingRow
              icon={MessageCircle}
              title={t("profile.feedback")}
              value={t("profile.feedbackHint")}
              onClick={() => openTelegramLink(bot)}
            />
          )}
          <li>
            <Link className="list-row" to="/privacy">
              <span className="icon-tile" aria-hidden="true">
                <ShieldCheck size={20} />
              </span>
              <span className="list-row__text">
                <strong>{t("profile.privacy")}</strong>
              </span>
              <ChevronRight className="list-row__chevron" size={20} />
            </Link>
          </li>
          <SettingRow icon={Trash2} title={t("profile.delete")} danger onClick={() => setSheet("delete")} />
        </ul>
      </section>

      {sheet === "nickname" && <NicknameSheet onClose={() => setSheet(null)} />}
      {sheet === "path" && <PathSheet onClose={() => setSheet(null)} />}
      {sheet === "language" && <LanguageSheet onClose={() => setSheet(null)} />}
      {sheet === "delete" && <DeleteSheet onClose={() => setSheet(null)} />}
    </main>
  );
}

function Stat({
  icon,
  value,
  label,
  note,
  tone,
}: {
  icon: ReactNode;
  value: string;
  label: string;
  note?: string;
  tone?: "amber" | "sky";
}) {
  return (
    <section className="card stat">
      <div className="stat__top">
        <span className={tone ? `icon-tile icon-tile--${tone}` : "icon-tile"} aria-hidden="true">
          {icon}
        </span>
        {note && <span className="hint small strong">{note}</span>}
      </div>
      <strong>{value}</strong>
      <span className="hint small">{label}</span>
    </section>
  );
}

function SettingRow({
  icon: Icon,
  title,
  value,
  danger,
  onClick,
}: {
  icon: LucideIcon;
  title: string;
  value?: string;
  danger?: boolean;
  onClick: () => void;
}) {
  return (
    <li>
      <button type="button" className="list-row" onClick={onClick}>
        <span className={danger ? "icon-tile chip--danger" : "icon-tile"} aria-hidden="true">
          <Icon size={20} />
        </span>
        <span className="list-row__text">
          <strong className={danger ? "error-text" : undefined}>{title}</strong>
          {value && <span className="hint small">{value}</span>}
        </span>
        <ChevronRight className="list-row__chevron" size={20} />
      </button>
    </li>
  );
}

function ReminderSetting() {
  const { t } = useTranslation();
  const { user, setUser } = useUser();
  const [saving, setSaving] = useState(false);
  const time = user.reminder_time.slice(0, 5);

  async function save(patch: { reminders_enabled?: boolean; reminder_time?: string }) {
    setSaving(true);
    try {
      // Reminders need the bot's permission to write (TZ 8.1).
      if (patch.reminders_enabled && !user.write_access && (await requestWriteAccess())) {
        await api.setWriteAccess(true);
      }
      setUser(await api.updateMe(patch));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="list-row" style={{ cursor: "default" }}>
      <span className="icon-tile icon-tile--amber" aria-hidden="true">
        <Bell size={20} />
      </span>
      <span className="list-row__text">
        <strong>{t("profile.reminders")}</strong>
        {user.reminders_enabled ? (
          <label className="row hint small">
            {t("profile.reminderAt")}
            <select
              className="select"
              value={time}
              disabled={saving}
              onChange={(e) => void save({ reminder_time: e.target.value })}
            >
              {REMINDER_TIMES.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </label>
        ) : (
          <span className="hint small">{t("profile.remindersOff")}</span>
        )}
        {user.reminders_enabled && !user.write_access && (
          <span className="small error-text">{t("profile.remindersNeedBot")}</span>
        )}
      </span>
      <Toggle
        checked={user.reminders_enabled}
        disabled={saving}
        label={t("profile.reminders")}
        onChange={(value) => void save({ reminders_enabled: value })}
      />
    </div>
  );
}

function SheetFrame({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  const { t } = useTranslation();
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label={title} onClick={onClose}>
      <div className="sheet stack" onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        {children}
        <button type="button" className="link-button" onClick={onClose}>
          {t("common.cancel")}
        </button>
      </div>
    </div>
  );
}

function NicknameSheet({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const { user, setUser } = useUser();
  const [value, setValue] = useState(user.nickname ?? "");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const lockedUntil = user.nickname_change_available_at ? new Date(user.nickname_change_available_at) : null;
  const locked = lockedUntil !== null && lockedUntil > new Date();

  async function save() {
    const formatError = nicknameFormatError(value);
    if (formatError) {
      setError(formatError);
      return;
    }
    setSaving(true);
    try {
      setUser(await api.changeNickname(value.trim()));
      haptic.success();
      onClose();
    } catch (e) {
      setError(e instanceof ApiError ? e.code : "unknown");
    } finally {
      setSaving(false);
    }
  }

  return (
    <SheetFrame title={t("profile.nickname")} onClose={onClose}>
      {locked ? (
        <p className="note">{t("profile.nicknameLocked", { date: lockedUntil!.toLocaleDateString() })}</p>
      ) : (
        <>
          <div className={error ? "input-wrap is-invalid" : "input-wrap"}>
            <span className="input-wrap__prefix">@</span>
            <input
              className="input"
              value={value}
              maxLength={32}
              autoComplete="off"
              spellCheck={false}
              onChange={(e) => {
                setValue(e.target.value);
                setError(null);
              }}
              aria-label={t("profile.nickname")}
            />
          </div>
          {error && (
            <p className="error-text small">
              {t(
                error === "nickname_change_too_soon"
                  ? "profile.nicknameTooSoon"
                  : `onboarding.nicknameErrors.${error.startsWith("nickname_") ? error : "unknown"}`,
              )}
            </p>
          )}
          <p className="hint small">{t("profile.nicknameRule")}</p>
          <button type="button" className="btn btn--block" disabled={saving || !value.trim()} onClick={() => void save()}>
            {t("common.save")}
          </button>
        </>
      )}
    </SheetFrame>
  );
}

function PathSheet({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const { user, setUser } = useUser();
  async function choose(path: UserPath) {
    setUser(await api.updateMe({ path }));
    onClose();
  }
  return (
    <SheetFrame title={t("profile.role")} onClose={onClose}>
      {PATHS.map((path) => (
        <button
          key={path}
          type="button"
          className={user.path === path ? "choice is-selected" : "choice"}
          onClick={() => void choose(path)}
        >
          <span className="choice__body">
            <span className="choice__title">{t(`roles.${path}`)}</span>
            <span className="hint small">{t(`onboarding.path.${path}Hint`)}</span>
          </span>
        </button>
      ))}
    </SheetFrame>
  );
}

function LanguageSheet({ onClose }: { onClose: () => void }) {
  const { t, i18n } = useTranslation();
  const { user, setUser } = useUser();
  async function choose(language: Language) {
    await i18n.changeLanguage(language);
    try {
      setUser(await api.updateMe({ language }));
    } catch {
      await i18n.changeLanguage(user.language);
    }
    onClose();
  }
  return (
    <SheetFrame title={t("profile.language")} onClose={onClose}>
      {LANGUAGES.map((language) => (
        <button
          key={language}
          type="button"
          className={user.language === language ? "choice is-selected" : "choice"}
          onClick={() => void choose(language)}
        >
          <span className="choice__title">{LANGUAGE_NAMES[language]}</span>
        </button>
      ))}
    </SheetFrame>
  );
}

function DeleteSheet({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const [deleting, setDeleting] = useState(false);
  const [done, setDone] = useState(false);

  async function remove() {
    setDeleting(true);
    try {
      await api.deleteMe();
      setDone(true);
      // Start over: the next login creates a fresh account and shows onboarding (QM-17).
      window.setTimeout(() => window.location.reload(), 1500);
    } catch {
      setDeleting(false);
    }
  }

  if (done) {
    return (
      <div className="overlay" role="dialog" aria-modal="true">
        <div className="sheet sheet--center stack">
          <span className="emoji" aria-hidden="true">
            🍃
          </span>
          <h2>{t("profile.deleted")}</h2>
        </div>
      </div>
    );
  }
  return (
    <SheetFrame title={t("profile.deleteTitle")} onClose={onClose}>
      <p className="text-2">{t("profile.deleteText")}</p>
      <button type="button" className="btn btn--block btn--danger" disabled={deleting} onClick={() => void remove()}>
        <Trash2 size={18} /> {t("profile.deleteConfirm")}
      </button>
    </SheetFrame>
  );
}
