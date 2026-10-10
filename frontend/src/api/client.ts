import type { components } from "./schema";

export type User = components["schemas"]["UserOut"];
type AuthOut = components["schemas"]["AuthOut"];
type MeUpdate = components["schemas"]["MeUpdate"];

let sessionToken: string | null = null;

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super(code);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (sessionToken) headers.set("Authorization", `Bearer ${sessionToken}`);

  const response = await fetch(`/api${path}`, { ...init, headers });
  if (!response.ok) {
    let code = `http_${response.status}`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") code = body.detail;
    } catch {
      // Non-JSON error body; keep the status-based code.
    }
    throw new ApiError(response.status, code);
  }
  return (await response.json()) as T;
}

export async function loginWithTelegram(initData: string): Promise<User> {
  const auth = await request<AuthOut>("/auth/telegram", {
    method: "POST",
    body: JSON.stringify({ init_data: initData }),
  });
  sessionToken = auth.token;
  return auth.user;
}

export function updateMe(patch: MeUpdate): Promise<User> {
  return request<User>("/me", { method: "PATCH", body: JSON.stringify(patch) });
}

/** Development only: signed fake initData so the app can be opened in a normal browser. */
export async function fetchDevInitData(languageCode: string): Promise<string> {
  const params = new URLSearchParams({ language_code: languageCode });
  const body = await request<{ init_data: string }>(`/dev/init-data?${params}`);
  return body.init_data;
}
