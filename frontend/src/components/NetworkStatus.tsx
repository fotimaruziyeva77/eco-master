import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, isReachable, onReachabilityChange } from "../api/client";
import { flush, pendingCount, subscribe } from "../outbox";
import { useUser } from "../state/user";
import { Emoji } from "./Emoji";

const PING_MS = 15_000;

/** Online unless the browser says so or the last request could not reach the server. */
function useOnline(): boolean {
  const read = () => navigator.onLine && isReachable();
  const [online, setOnline] = useState(read);
  useEffect(() => {
    const update = () => {
      setOnline(read());
      // The browser says the network is back: ask the server right away.
      if (navigator.onLine && !isReachable()) void api.health().catch(() => {});
    };
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    const stop = onReachabilityChange(update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
      stop();
    };
  }, []);
  return online;
}

function usePending(): number {
  const [count, setCount] = useState(pendingCount);
  useEffect(() => subscribe(() => setCount(pendingCount())), []);
  return count;
}

/**
 * Tells the user when the connection is gone, and sends what was done meanwhile once it is
 * back (TZ 13, QM-18).
 */
export function NetworkStatus() {
  const { t } = useTranslation();
  const { setUser } = useUser();
  const online = useOnline();
  const pending = usePending();
  const before = useRef(pending);
  const [synced, setSynced] = useState(false);

  // On start and whenever the connection returns.
  useEffect(() => {
    if (online) void flush();
  }, [online]);

  // While the server is unreachable, check now and then whether it is back.
  useEffect(() => {
    if (online) return;
    const timer = window.setInterval(() => void api.health().catch(() => {}), PING_MS);
    return () => window.clearInterval(timer);
  }, [online]);

  useEffect(() => {
    const sentEverything = before.current > 0 && pending === 0;
    before.current = pending;
    if (!sentEverything) return;
    void api.me().then(setUser, () => {});
    setSynced(true);
    const timer = window.setTimeout(() => setSynced(false), 4000);
    return () => window.clearTimeout(timer);
  }, [pending, setUser]);

  if (!online) {
    return (
      <div className="net-banner" role="status">
        <Emoji char="📡" /> {t("network.offline")}
      </div>
    );
  }
  if (synced) {
    return (
      <div className="net-banner net-banner--ok" role="status">
        ✓ {t("network.synced")}
      </div>
    );
  }
  return null;
}
