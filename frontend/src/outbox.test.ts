import { beforeEach, describe, expect, it, vi } from "vitest";

// What was done offline waits on the device and is sent once the connection is back,
// with the same idempotency key, so points are written exactly once (TZ 13, QM-18).

const store = new Map<string, string>();
vi.stubGlobal("localStorage", {
  getItem: (key: string) => store.get(key) ?? null,
  setItem: (key: string, value: string) => void store.set(key, value),
});
vi.stubGlobal("window", { setTimeout: vi.fn(() => 1) });

const { projectDone, dailyDone } = vi.hoisted(() => ({ projectDone: vi.fn(), dailyDone: vi.fn() }));
vi.mock("./api/client", () => {
  class ApiError extends Error {
    constructor(
      readonly status: number,
      readonly code: string,
    ) {
      super(code);
    }
  }
  return { ApiError, api: { projectDone, dailyDone } };
});

const { ApiError } = await import("./api/client");
const outbox = await import("./outbox");

const offline = () => Promise.reject(new TypeError("Failed to fetch"));

beforeEach(() => {
  store.clear();
  projectDone.mockReset();
  dailyDone.mockReset();
});

describe("offline outbox", () => {
  it("keeps actions on the device", () => {
    outbox.enqueue({ id: "a", kind: "project_done", slug: "compost" });
    outbox.enqueue({ id: "a", kind: "project_done", slug: "compost" }); // same tap twice
    outbox.enqueue({ id: "b", kind: "daily_done" });
    expect(outbox.pendingCount()).toBe(2);
    expect(JSON.parse(store.get("ekoustoz.outbox.v1")!)).toHaveLength(2);
  });

  it("waits while there is no connection", async () => {
    outbox.enqueue({ id: "a", kind: "daily_done" });
    dailyDone.mockImplementation(offline);
    await outbox.flush();
    expect(outbox.pendingCount()).toBe(1);
  });

  it("sends with the same idempotency key once the connection is back", async () => {
    outbox.enqueue({ id: "event-1", kind: "project_done", slug: "compost" });
    outbox.enqueue({ id: "event-2", kind: "daily_done" });
    projectDone.mockResolvedValue({ awarded: true });
    dailyDone.mockResolvedValue({ awarded: true });
    await outbox.flush();
    expect(projectDone).toHaveBeenCalledWith("compost", "event-1");
    expect(dailyDone).toHaveBeenCalledWith("event-2");
    expect(outbox.pendingCount()).toBe(0);
  });

  it("drops what the server refuses for good, keeps what may still go through", async () => {
    outbox.enqueue({ id: "gone", kind: "project_done", slug: "unpublished" });
    projectDone.mockRejectedValue(new ApiError(404, "project_not_found"));
    await outbox.flush();
    expect(outbox.pendingCount()).toBe(0);

    outbox.enqueue({ id: "later", kind: "daily_done" });
    dailyDone.mockRejectedValue(new ApiError(503, "http_503")); // server down: try again later
    await outbox.flush();
    dailyDone.mockRejectedValue(new ApiError(401, "invalid_token")); // session expired: retry after login
    await outbox.flush();
    expect(outbox.pendingCount()).toBe(1);
  });

  it("tells listeners when the queue changes", async () => {
    const listener = vi.fn();
    const stop = outbox.subscribe(listener);
    outbox.enqueue({ id: "a", kind: "daily_done" });
    dailyDone.mockResolvedValue({ awarded: true });
    await outbox.flush();
    stop();
    expect(listener).toHaveBeenCalledTimes(2);
  });
});
