import type { components } from "./schema";

type Schemas = components["schemas"];
export type User = Schemas["UserOut"];
export type UserPath = NonNullable<User["path"]>;
export type Language = User["language"];
export type Home = Schemas["HomeOut"];
export type Category = Schemas["CategoryOut"];
export type CategoryDetail = Schemas["CategoryDetailOut"];
export type ProjectSummary = Schemas["ProjectSummaryOut"];
export type ProjectDetail = Schemas["ProjectDetailOut"];
export type CardSummary = Schemas["CardSummaryOut"];
export type CardDetail = Schemas["CardDetailOut"];
export type DoneResult = Schemas["DoneOut"];

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

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

export async function loginWithTelegram(initData: string): Promise<User> {
  const auth = await post<Schemas["AuthOut"]>("/auth/telegram", { init_data: initData });
  sessionToken = auth.token;
  return auth.user;
}

/** Development only: signed fake initData so the app can be opened in a normal browser. */
export async function fetchDevInitData(languageCode: string): Promise<string> {
  const params = new URLSearchParams({ language_code: languageCode });
  const body = await request<{ init_data: string }>(`/dev/init-data?${params}`);
  return body.init_data;
}

export const api = {
  updateMe: (patch: Schemas["MeUpdate"]) =>
    request<User>("/me", { method: "PATCH", body: JSON.stringify(patch) }),
  setWriteAccess: (granted: boolean) => post<User>("/me/write-access", { granted }),

  onboardingLanguage: (language: Language) => post<User>("/onboarding/language", { language }),
  onboardingPath: (path: UserPath) => post<User>("/onboarding/path", { path }),
  onboardingNickname: (nickname: string) => post<User>("/onboarding/nickname", { nickname }),
  onboardingComplete: () => post<User>("/onboarding/complete"),
  checkNickname: (value: string) =>
    request<Schemas["NicknameCheckOut"]>(
      `/onboarding/nickname-check?${new URLSearchParams({ value })}`,
    ),

  home: () => request<Home>("/home"),
  categories: () => request<Category[]>("/categories"),
  category: (code: string) => request<CategoryDetail>(`/categories/${encodeURIComponent(code)}`),
  project: (slug: string) => request<ProjectDetail>(`/projects/${encodeURIComponent(slug)}`),
  projectDone: (slug: string, clientEventId: string) =>
    post<DoneResult>(`/projects/${encodeURIComponent(slug)}/done`, {
      client_event_id: clientEventId,
    }),
  cards: () => request<CardSummary[]>("/cards"),
  card: (slug: string) => request<CardDetail>(`/cards/${encodeURIComponent(slug)}`),
};
