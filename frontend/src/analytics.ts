import { api, hasSession } from "./api/client";

/** Events the server can not see itself (TZ 14): video plays and client-side errors. */
type ClientEvent =
  | { name: "video_play" | "video_complete"; props: { project: string } }
  | { name: "error"; props: { type: string; screen: string } };

const BATCH = 20;
const FLUSH_DELAY_MS = 3000;
// A broken page must not flood the server with the same error.
const MAX_ERRORS_PER_SESSION = 20;

let queue: ClientEvent[] = [];
let timer = 0;
let errorsSent = 0;

function schedule(): void {
  if (!timer) timer = window.setTimeout(() => void flush(), FLUSH_DELAY_MS);
}

async function flush(): Promise<void> {
  timer = 0;
  if (!queue.length) return;
  if (!hasSession()) {
    queue = queue.slice(-BATCH); // wait for the sign-in, keep only the latest
    schedule();
    return;
  }
  const batch = queue.splice(0, BATCH);
  try {
    await api.events(batch);
  } catch {
    // Analytics never gets in the user's way.
  }
  if (queue.length) schedule();
}

export function trackVideo(name: "video_play" | "video_complete", project: string): void {
  queue.push({ name, props: { project } });
  schedule();
}

export function trackError(type: string): void {
  if (errorsSent >= MAX_ERRORS_PER_SESSION) return;
  errorsSent += 1;
  // Only the route path: no query strings, nothing typed by the user.
  queue.push({ name: "error", props: { type: type.slice(0, 64), screen: location.pathname.slice(0, 64) } });
  schedule();
}

/** Uncaught errors anywhere in the app. */
export function watchErrors(): void {
  window.addEventListener("error", () => trackError("js"));
  window.addEventListener("unhandledrejection", () => trackError("promise"));
}
