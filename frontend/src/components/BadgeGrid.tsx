import { useTranslation } from "react-i18next";

import { api } from "../api/client";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";
import { InlineError, InlineLoading } from "./common";

/** Earned badges in colour; the rest greyed out with the rule to earn them (TZ 8.6). */
export function BadgeGrid() {
  const { t } = useTranslation();
  const tr = useTr();
  const badges = useLoad(() => api.myBadges(), []);

  if (badges.loading && !badges.data) return <InlineLoading />;
  if (badges.error !== undefined && !badges.data) {
    return <InlineError error={badges.error} onRetry={badges.reload} />;
  }
  return (
    <ul className="badge-grid">
      {(badges.data ?? []).map((badge) => {
        const earned = Boolean(badge.earned_at);
        return (
          <li key={badge.code} className={earned ? "badge-tile" : "badge-tile is-locked"}>
            <span className="badge-tile__icon" aria-hidden="true">
              {badge.icon}
            </span>
            <strong>{tr(badge.name)}</strong>
            <span className="hint small">{earned ? "✓" : tr(badge.description)}</span>
            {!earned && <span className="visually-hidden">{t("badges.locked")}</span>}
          </li>
        );
      })}
    </ul>
  );
}
