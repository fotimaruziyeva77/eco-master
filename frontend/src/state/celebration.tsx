import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { api, type Badge } from "../api/client";
import { Confetti } from "../components/Confetti";
import { Emoji } from "../components/Emoji";
import { Medal } from "../components/Medal";
import { ShareButton } from "../components/ShareButton";
import { LEVEL_EMOJI } from "../components/ui";
import { useTr } from "../i18n/tr";
import { sound } from "../sound";
import { haptic } from "../telegram";
import { useUser } from "./user";

type Celebrate = (badges: Badge[]) => void;
type Moment = { kind: "badge"; badge: Badge } | { kind: "level"; code: string };

const CelebrationContext = createContext<Celebrate>(() => {});

/**
 * Shows a new badge (TZ 8.6) or a new level the moment it is earned: a medal or the level's
 * picture, confetti and a short fanfare.
 */
export function CelebrationProvider({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const tr = useTr();
  const { user, setUser } = useUser();
  const [queue, setQueue] = useState<Moment[]>([]);

  const celebrate = useCallback<Celebrate>((badges) => {
    if (!badges.length) return;
    haptic.success();
    setQueue((q) => [...q, ...badges.map((badge) => ({ kind: "badge" as const, badge }))]);
  }, []);

  // Points past the next level's threshold: ask the server for the new level, then celebrate.
  const nextLevelAt = user.level.next_min_points;
  const levelCode = user.level.code;
  useEffect(() => {
    if (nextLevelAt === null || nextLevelAt === undefined || user.points_total < nextLevelAt) return;
    let alive = true;
    api.me().then(
      (fresh) => {
        if (!alive) return;
        setUser(fresh);
        if (fresh.level.code !== levelCode) {
          haptic.success();
          setQueue((q) => [...q, { kind: "level", code: fresh.level.code }]);
        }
      },
      () => {},
    );
    return () => {
      alive = false;
    };
  }, [user.points_total, nextLevelAt, levelCode, setUser]);

  const current = queue[0];
  useEffect(() => {
    if (current) sound.fanfare();
  }, [current]);

  const close = () => setQueue((q) => q.slice(1));
  return (
    <CelebrationContext.Provider value={celebrate}>
      {children}
      {current && (
        <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="celebrate-title">
          <Confetti />
          <div className="sheet sheet--center stack">
            {current.kind === "badge" ? (
              <>
                <div className="celebrate__medal">
                  <Medal icon={current.badge.icon} size="lg" />
                </div>
                <span className="chip chip--amber" style={{ justifySelf: "center" }}>
                  {t("badges.newTitle")}
                </span>
                <h2 id="celebrate-title">{tr(current.badge.name)}</h2>
                <p className="hint">{tr(current.badge.description)}</p>
              </>
            ) : (
              <>
                <div className="celebrate__level" aria-hidden="true">
                  <Emoji char={LEVEL_EMOJI[current.code] ?? "🌱"} />
                </div>
                <span className="chip chip--amber" style={{ justifySelf: "center" }}>
                  {t("levels.newTitle")}
                </span>
                <h2 id="celebrate-title">{t(`levels.${current.code}`)}</h2>
              </>
            )}
            <button type="button" className="btn btn--block" onClick={close} autoFocus>
              {t("badges.ok")}
            </button>
            {current.kind === "badge" ? (
              <ShareButton kind="badge" objectId={current.badge.code} />
            ) : (
              <ShareButton kind="progress" label={t("share.progress")} />
            )}
          </div>
        </div>
      )}
    </CelebrationContext.Provider>
  );
}

export function useCelebrate(): Celebrate {
  return useContext(CelebrationContext);
}
