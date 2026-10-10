import { CircleCheck, Lock } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { Badge } from "../api/client";
import { useTr } from "../i18n/tr";

/** Earned badges in colour; the rest greyed out with progress or the rule (TZ 8.6). */
export function BadgeGrid({ badges }: { badges: Badge[] }) {
  const { t } = useTranslation();
  const tr = useTr();
  return (
    <ul className="badge-grid">
      {badges.map((badge) => {
        const earned = Boolean(badge.earned_at);
        const current = badge.progress_current ?? 0;
        const target = badge.progress_target ?? 0;
        return (
          <li
            key={badge.code}
            className={earned ? "badge-tile" : "badge-tile is-locked"}
            title={tr(badge.description)}
          >
            <span className="badge-tile__icon" aria-hidden="true">
              {badge.icon}
            </span>
            <strong>{tr(badge.name)}</strong>
            {earned ? (
              <small className="row is-earned">
                <CircleCheck size={13} /> {t("badges.earned")}
              </small>
            ) : target > 1 && current > 0 ? (
              <small>
                {current} / {target}
              </small>
            ) : (
              <small className="row">
                <Lock size={12} /> {t("badges.locked")}
              </small>
            )}
          </li>
        );
      })}
    </ul>
  );
}
