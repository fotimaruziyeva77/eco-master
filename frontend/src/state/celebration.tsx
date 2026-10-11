import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { Badge } from "../api/client";
import { ShareButton } from "../components/ShareButton";
import { Medal } from "../components/Medal";
import { useTr } from "../i18n/tr";
import { haptic } from "../telegram";

type Celebrate = (badges: Badge[]) => void;

const CelebrationContext = createContext<Celebrate>(() => {});

/** Shows a "new badge" dialog whenever an action earns one (TZ 8.6). */
export function CelebrationProvider({ children }: { children: ReactNode }) {
  const { t } = useTranslation();
  const tr = useTr();
  const [queue, setQueue] = useState<Badge[]>([]);

  const celebrate = useCallback<Celebrate>((badges) => {
    if (!badges.length) return;
    haptic.success();
    setQueue((q) => [...q, ...badges]);
  }, []);

  const current = queue[0];
  return (
    <CelebrationContext.Provider value={celebrate}>
      {children}
      {current && (
        <div className="overlay" role="dialog" aria-modal="true" aria-labelledby="badge-title">
          <div className="sheet sheet--center stack">
            <div className="celebrate__medal">
              <Medal icon={current.icon} size="lg" />
            </div>
            <span className="chip chip--amber" style={{ justifySelf: "center" }}>
              {t("badges.newTitle")}
            </span>
            <h2 id="badge-title">{tr(current.name)}</h2>
            <p className="hint">{tr(current.description)}</p>
            <button
              type="button"
              className="btn btn--block"
              onClick={() => setQueue((q) => q.slice(1))}
              autoFocus
            >
              {t("badges.ok")}
            </button>
            <ShareButton kind="badge" objectId={current.code} />
          </div>
        </div>
      )}
    </CelebrationContext.Provider>
  );
}

export function useCelebrate(): Celebrate {
  return useContext(CelebrationContext);
}
