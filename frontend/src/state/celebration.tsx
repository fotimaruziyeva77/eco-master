import { createContext, useCallback, useContext, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import type { Badge } from "../api/client";
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
          <div className="dialog">
            <div className="emoji emoji--large" aria-hidden="true">
              {current.icon}
            </div>
            <p className="hint">{t("badges.newTitle")}</p>
            <h2 id="badge-title">{tr(current.name)}</h2>
            <p className="hint">{tr(current.description)}</p>
            <button
              type="button"
              className="button button--block"
              onClick={() => setQueue((q) => q.slice(1))}
              autoFocus
            >
              {t("badges.ok")}
            </button>
          </div>
        </div>
      )}
    </CelebrationContext.Provider>
  );
}

export function useCelebrate(): Celebrate {
  return useContext(CelebrationContext);
}
