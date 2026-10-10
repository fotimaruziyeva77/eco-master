import { api, ApiError } from "./api/client";

/**
 * Actions done without a connection (TZ 13, QM-18). They wait on the device and are sent
 * again when the connection is back, with the same idempotency key, so the points are
 * written exactly once.
 */
export type PendingAction =
  | { id: string; kind: "project_done"; slug: string }
  | { id: string; kind: "daily_done" };

const KEY = "ekoustoz.outbox.v1";
const RETRY_MS = 20_000;
// Answers the server will never accept: retrying them forever would not help.
const FINAL = new Set([400, 403, 404, 409, 422]);

const listeners = new Set<() => void>();
let memory: PendingAction[] = [];
let flushing = false;
let timer = 0;

function read(): PendingAction[] {
  try {
    const saved: unknown = JSON.parse(localStorage.getItem(KEY) ?? "[]");
    return Array.isArray(saved) ? (saved as PendingAction[]) : [];
  } catch {
    return memory; // storage blocked: keep them for this session at least
  }
}

function write(items: PendingAction[]): void {
  memory = items;
  try {
    localStorage.setItem(KEY, JSON.stringify(items));
  } catch {
    // Kept in memory instead.
  }
  listeners.forEach((listener) => listener());
}

function schedule(): void {
  if (timer) return;
  timer = window.setTimeout(() => {
    timer = 0;
    void flush();
  }, RETRY_MS);
}

export function pendingCount(): number {
  return read().length;
}

export function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function enqueue(action: PendingAction): void {
  write([...read().filter((a) => a.id !== action.id), action]);
  schedule();
}

/** Send what is waiting; stops at the first network failure and tries again later. */
export async function flush(): Promise<void> {
  if (flushing) return;
  flushing = true;
  try {
    for (const action of read()) {
      try {
        if (action.kind === "project_done") await api.projectDone(action.slug, action.id);
        else await api.dailyDone(action.id);
      } catch (error) {
        if (!(error instanceof ApiError && FINAL.has(error.status))) {
          schedule();
          return;
        }
      }
      write(read().filter((a) => a.id !== action.id));
    }
  } finally {
    flushing = false;
  }
}
