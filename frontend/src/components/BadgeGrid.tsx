import { CircleCheck } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { Badge } from "../api/client";
import { useTr } from "../i18n/tr";
import { Medal } from "./Medal";
import { ProgressBar } from "./ui";

/**
 * Earned badges as gold medals, the rest grey with their progress (TZ 8.6). A tap shows how
 * to earn one: a reason to come back.
 */
export function BadgeGrid({ badges }: { badges: Badge[] }) {
  const tr = useTr();
  const [open, setOpen] = useState<Badge | null>(null);
  return (
    <>
      <ul className="badge-grid">
        {badges.map((badge) => {
          const earned = Boolean(badge.earned_at);
          const current = badge.progress_current ?? 0;
          const target = badge.progress_target ?? 0;
          return (
            <li key={badge.code}>
              <button
                type="button"
                className={earned ? "badge-tile" : "badge-tile is-locked"}
                onClick={() => setOpen(badge)}
              >
                <Medal icon={badge.icon} locked={!earned} />
                <strong>{tr(badge.name)}</strong>
                {!earned && target > 1 && current > 0 && (
                  <small>
                    {current} / {target}
                  </small>
                )}
              </button>
            </li>
          );
        })}
      </ul>
      {open && <BadgeSheet badge={open} onClose={() => setOpen(null)} />}
    </>
  );
}

function BadgeSheet({ badge, onClose }: { badge: Badge; onClose: () => void }) {
  const { t } = useTranslation();
  const tr = useTr();
  const earned = Boolean(badge.earned_at);
  const current = badge.progress_current ?? 0;
  const target = badge.progress_target ?? 0;
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label={tr(badge.name)} onClick={onClose}>
      <div className="sheet sheet--center stack" onClick={(e) => e.stopPropagation()}>
        <div className="celebrate__medal">
          <Medal icon={badge.icon} locked={!earned} size="lg" />
        </div>
        <h2>{tr(badge.name)}</h2>
        <p className="text-2">{tr(badge.description)}</p>
        {earned ? (
          <span className="ok-text row" style={{ justifyContent: "center" }}>
            <CircleCheck size={18} /> {t("badges.earned")}
          </span>
        ) : (
          target > 1 && (
            <div className="stack" style={{ gap: 6 }}>
              <ProgressBar value={current} max={target} />
              <span className="hint small strong">
                {current} / {target}
              </span>
            </div>
          )
        )}
        <button type="button" className="btn btn--block" onClick={onClose}>
          {t("badges.ok")}
        </button>
      </div>
    </div>
  );
}
