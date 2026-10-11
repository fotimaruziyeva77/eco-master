import { useTranslation } from "react-i18next";

import type { User } from "../api/client";
import { Emoji } from "./Emoji";
import { LEVEL_EMOJI, levelProgress, ProgressBar } from "./ui";

/** Level in one row: picture, name, points to the next level and the next level's picture. */
export function LevelProgress({ user }: { user: User }) {
  const { t } = useTranslation();
  const level = levelProgress(user);

  return (
    <section className="card level-row">
      <span className="level-emoji" aria-hidden="true">
        <Emoji char={LEVEL_EMOJI[level.code]} />
      </span>
      <div className="level-row__main">
        <div className="level-row__top">
          <strong>{t(`levels.${level.code}`)}</strong>
          <span className="level-row__points">
            <Emoji char="⭐" /> {user.points_total}
            {level.next && <span className="hint"> / {level.next}</span>}
          </span>
        </div>
        <ProgressBar value={level.percent} max={100} />
      </div>
      {level.nextCode ? (
        <span className="level-row__next" title={t("home.nextLevel", { name: t(`levels.${level.nextCode}`) })}>
          <Emoji char={LEVEL_EMOJI[level.nextCode]} label={t("home.nextLevel", { name: t(`levels.${level.nextCode}`) })} />
        </span>
      ) : (
        <span className="level-row__next" title={t("home.topLevel")}>
          <Emoji char="👑" label={t("home.topLevel")} />
        </span>
      )}
    </section>
  );
}
