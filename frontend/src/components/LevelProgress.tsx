import { useTranslation } from "react-i18next";

import type { User } from "../api/client";

export function LevelProgress({ user }: { user: User }) {
  const { t } = useTranslation();
  const { code, min_points: min, next_min_points: next } = user.level;
  const points = user.points_total;
  const percent = next ? Math.min(100, Math.round(((points - min) / (next - min)) * 100)) : 100;

  return (
    <div className="level">
      <div className="level__row">
        <span className="level__name">{t(`levels.${code}`)}</span>
        <span className="level__points">{t("home.points", { count: points })}</span>
      </div>
      <div
        className="progress"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <div className="progress__bar" style={{ width: `${percent}%` }} />
      </div>
      <p className="hint level__next">
        {next ? t("home.toNextLevel", { count: next - points }) : t("home.topLevel")}
      </p>
    </div>
  );
}
