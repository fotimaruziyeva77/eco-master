import { useCallback, useEffect, useState } from "react";

type LoadState<T> = { data?: T; error?: unknown; loading: boolean };

/** Load data for a screen; `reload` retries after an error. */
export function useLoad<T>(load: () => Promise<T>, deps: readonly unknown[]) {
  const [state, setState] = useState<LoadState<T>>({ loading: true });
  const [attempt, setAttempt] = useState(0);

  const run = useCallback(load, deps);

  useEffect(() => {
    let alive = true;
    setState((s) => ({ data: s.data, loading: true }));
    run().then(
      (data) => alive && setState({ data, loading: false }),
      (error: unknown) => alive && setState({ error, loading: false }),
    );
    return () => {
      alive = false;
    };
  }, [run, attempt]);

  const reload = useCallback(() => setAttempt((n) => n + 1), []);
  return { ...state, reload };
}
