import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { User } from "../api/client";
import { Emoji } from "./Emoji";
import { Tree } from "./Tree";
import { LEVEL_EMOJI, levelProgress, ProgressBar } from "./ui";

/** Level in one row: the user's tree, level name, points to the next level and its picture.
 * Opens the profile, where the tree is big. */
export function LevelProgress({ user }: { user: User }) {
  const { t } = useTranslation();
  const level = levelProgress(user);

  return (
    <Link to="/profile" className="card level-row">
      <span className="level-tree" aria-hidden="true">
        <Tree points={user.points_total} size={56} fit />
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
    </Link>
  );
}
