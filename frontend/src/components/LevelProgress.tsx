import { CircleCheck } from "lucide-react";
import { useTranslation } from "react-i18next";

import type { User } from "../api/client";
import { LEVEL_EMOJI, levelProgress, ProgressBar } from "./ui";

/** Level card (design: bosh_sahifa): stage, level name, points to the next level. */
export function LevelProgress({ user }: { user: User }) {
  const { t } = useTranslation();
  const level = levelProgress(user);

  return (
    <section className="card">
      <div className="level-card__top">
        <span className="level-emoji" aria-hidden="true">
          {LEVEL_EMOJI[level.code]}
        </span>
        <div className="level-card__name">
          <span className="hint small">{t("home.stage", { n: level.index })}</span>
          <strong>{t(`levels.${level.code}`)}</strong>
        </div>
        <div className="level-card__points">
          <strong>{user.points_total}</strong>
          {level.next && <span className="hint"> / {level.next}</span>}
          <div className="hint small">{t("home.pointsWord", { count: user.points_total })}</div>
        </div>
      </div>
      <div style={{ marginTop: 14 }}>
        <ProgressBar value={level.percent} max={100} />
      </div>
      <div className="level-card__foot">
        <span className="row text-2">
          <CircleCheck size={15} />
          {level.next ? t("home.filled", { percent: level.percent }) : t("home.topLevel")}
        </span>
        {level.nextCode && (
          <span className="ok-text">
            {t("home.nextLevel", { name: t(`levels.${level.nextCode}`) })} {LEVEL_EMOJI[level.nextCode]}
          </span>
        )}
      </div>
    </section>
  );
}
