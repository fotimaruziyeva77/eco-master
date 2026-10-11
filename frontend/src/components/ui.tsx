import { ArrowLeft } from "lucide-react";
import type { CSSProperties, ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { User } from "../api/client";
import mark from "../assets/brand/eco-master-mark.webp";
import { Emoji } from "./Emoji";
import { useUser } from "../state/user";
import { insideTelegram, useTelegramBackButton } from "../telegram";

// No profile photos are collected (TZ 11.2), so everyone gets a friendly animal picked from their id.
const AVATAR_EMOJI = ["🦊", "🐼", "🐢", "🦉", "🐝", "🦋", "🐞", "🐬", "🦔", "🐸", "🐨", "🦁"];
const AVATAR_BG = ["#d1fae5", "#fef3c7", "#e0f2fe", "#ede9fe", "#fce7f3", "#ecfccb"];

export function Avatar({ id, size = "md" }: { id: number; size?: "md" | "lg" | "xl" }) {
  const emoji = AVATAR_EMOJI[id % AVATAR_EMOJI.length];
  const background = AVATAR_BG[Math.floor(id / AVATAR_EMOJI.length) % AVATAR_BG.length];
  const className = size === "md" ? "avatar" : `avatar avatar--${size}`;
  return (
    <span className={className} style={{ background }} aria-hidden="true">
      <Emoji char={emoji} />
    </span>
  );
}

export const LEVEL_ORDER = ["seed", "beginner", "young_ecologist", "helper", "ekoustoz"] as const;
export const LEVEL_EMOJI: Record<string, string> = {
  seed: "🌰",
  beginner: "🌱",
  young_ecologist: "🌿",
  helper: "🌳",
  ekoustoz: "🏆",
};

export function nextLevelCode(code: string): string | null {
  const i = LEVEL_ORDER.indexOf(code as (typeof LEVEL_ORDER)[number]);
  return i >= 0 && i + 1 < LEVEL_ORDER.length ? LEVEL_ORDER[i + 1] : null;
}

/** Brand, streak and points on top of every tab screen (design: bosh_sahifa). */
export function TopBar({ subtitle }: { subtitle: string }) {
  const { t } = useTranslation();
  const { user } = useUser();
  return (
    <header className="topbar">
      <div className="topbar__brand">
        <img className="logo" src={mark} alt="" />
        <span className="topbar__title">
          <strong>{t("common.appName")}</strong>
          <span>{subtitle}</span>
        </span>
      </div>
      <span className="chip chip--amber" aria-label={t("home.streak", { count: user.streak_current })}>
        <Emoji char="🔥" /> {user.streak_current}
      </span>
      <span className="chip" aria-label={t("home.points", { count: user.points_total })}>
        <Emoji char="⭐" /> {user.points_total}
      </span>
      <Link to="/profile" aria-label={t("nav.profile")}>
        <Avatar id={user.id} />
      </Link>
    </header>
  );
}

/** Header of a nested screen: Telegram's own back button inside Telegram, an arrow in a browser. */
export function SubpageHeader({ title, onBack, right }: { title?: ReactNode; onBack: () => void; right?: ReactNode }) {
  const { t } = useTranslation();
  useTelegramBackButton(onBack);
  return (
    <header className="topbar">
      {!insideTelegram() && (
        <button className="icon-button" type="button" onClick={onBack} aria-label={t("common.back")}>
          <ArrowLeft size={22} />
        </button>
      )}
      <div className="topbar__brand">
        <img className="logo" src={mark} alt="" />
        {title && (
          <span className="topbar__title">
            <strong>{title}</strong>
          </span>
        )}
      </div>
      {right}
    </header>
  );
}

export function ProgressBar({ value, max, tone, thin }: { value: number; max: number; tone?: "amber"; thin?: boolean }) {
  const percent = max > 0 ? Math.max(0, Math.min(100, Math.round((value / max) * 100))) : 0;
  const className = ["progress", tone === "amber" && "progress--amber", thin && "progress--thin"]
    .filter(Boolean)
    .join(" ");
  return (
    <div className={className} role="progressbar" aria-valuemin={0} aria-valuemax={max} aria-valuenow={value}>
      <div className="progress__bar" style={{ width: `${percent}%` }} />
    </div>
  );
}

export function Toggle({
  checked,
  onChange,
  label,
  disabled,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      className="toggle"
      disabled={disabled}
      onClick={() => onChange(!checked)}
    />
  );
}

/** Light tint of a category colour for chips and icon tiles. */
export function tint(color: string, alpha = "26"): CSSProperties {
  return { background: `${color}${alpha}` };
}

export function levelProgress(user: User) {
  const { code, min_points: min, next_min_points: next } = user.level;
  const points = user.points_total;
  return {
    code,
    next,
    nextCode: nextLevelCode(code),
    percent: next ? Math.round(((points - min) / (next - min)) * 100) : 100,
    index: LEVEL_ORDER.indexOf(code as (typeof LEVEL_ORDER)[number]) + 1,
  };
}
