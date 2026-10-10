import type { components } from "../api/schema";

type S = components["schemas"];
export type AdminMe = S["AdminMeOut"];
export type AdminRow = S["AdminOut"];
export type LoginResult = S["LoginOut"];
export type ContentTypeInfo = S["ContentTypeOut"];
export type ContentMeta = S["ContentMetaOut"];
export type FieldSpec = S["FieldSpecOut"];
export type ContentRow = S["ContentRowOut"];
export type ContentItem = S["ContentItemOut"];
export type Issue = S["IssueOut"];
export type ContentStatus = NonNullable<ContentItem["status"]>;
export type Schedule = S["ScheduleOut"];
export type UserRow = S["AdminUserRowOut"];
export type UserDetail = S["AdminUserDetailOut"];
export type ActivityRow = S["ActivityRowOut"];
export type Report = S["ReportOut"];
export type ReportGroup = S["ReportGroupOut"];
export type Word = S["WordOut"];
export type WordKind = Word["kind"];
export type Stats = S["AdminStatsOut"];
export type QuestionStat = S["QuestionStatOut"];
export type Flags = S["FlagsOut"];
export type AuditPage = S["AuditPageOut"];
export type AuditRow = S["AuditRowOut"];
export type AdminRole = AdminMe["role"];
export type MarketCounts = S["MarketCountsOut"];
export type MarketRow = S["MarketRowOut"];
export type MarketListing = S["MarketListingOut"];
export type MarketDecision = S["MarketDecisionIn"];
export type MarketReason = MarketDecision["reason"];
export type HandoverPoint = S["HandoverPointOut"];
export type HandoverDesk = S["HandoverDeskOut"];
export type HandoverItem = S["HandoverItemOut"];
export type HandoverMatch = S["HandoverMatchOut"];
export type MarketFilter = "pending" | "reported" | "approved" | "rejected" | "hidden" | "handover" | "all";

/** Values of a content form: {"uz": ..., "ru": ..., "en": ...} for multilingual fields. */
export type Values = Record<string, unknown>;

export class AdminApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: unknown,
  ) {
    super(typeof detail === "string" ? detail : `http_${status}`);
  }

  /** Field errors of a 422 "invalid" answer. */
  get fieldErrors(): Record<string, string> {
    const d = this.detail as { code?: string; errors?: Record<string, string> } | null;
    return d && typeof d === "object" && d.errors ? d.errors : {};
  }

  /** Issues of a 422 "publish_blocked" answer. */
  get issues(): Issue[] {
    const d = this.detail as { code?: string; issues?: Issue[] } | null;
    return d && typeof d === "object" && d.issues ? d.issues : [];
  }
}

let onSignedOut: (() => void) | null = null;

/** Called when the session ends (expired cookie, deactivated account). */
export function setSignedOutHandler(handler: () => void): void {
  onSignedOut = handler;
}

async function call<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined) headers.set("Content-Type", "application/json");
  const response = await fetch(`/api/admin${path}`, { ...init, headers, credentials: "same-origin" });
  if (!response.ok) {
    let detail: unknown = `http_${response.status}`;
    try {
      detail = ((await response.json()) as { detail?: unknown }).detail ?? detail;
    } catch {
      // Not JSON; keep the status code.
    }
    if (response.status === 401 && !path.startsWith("/auth/")) onSignedOut?.();
    throw new AdminApiError(response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const get = <T>(path: string) => call<T>(path);
const send = <T>(method: string, path: string, body?: unknown) =>
  call<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });

function query(params: Record<string, string | number | null | undefined>): string {
  const q = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== null && value !== undefined && value !== "") q.set(key, String(value));
  }
  const text = q.toString();
  return text ? `?${text}` : "";
}

export const adminApi = {
  login: (login: string, password: string) => send<LoginResult>("POST", "/auth/login", { login, password }),
  code: (token: string, code: string) => send<AdminMe>("POST", "/auth/code", { token, code }),
  me: () => get<AdminMe>("/auth/me"),
  logout: () => send<void>("POST", "/auth/logout"),
  changePassword: (current: string, next: string) =>
    send<AdminMe>("POST", "/auth/password", { current, new: next }),

  contentTypes: () => get<ContentTypeInfo[]>("/content"),
  contentMeta: (type: string) => get<ContentMeta>(`/content/${type}/meta`),
  contentList: (type: string, status: string | null, q: string) =>
    get<ContentRow[]>(`/content/${type}${query({ status, q })}`),
  contentItem: (type: string, id: number) => get<ContentItem>(`/content/${type}/${id}`),
  contentCreate: (type: string, values: Values) => send<ContentItem>("POST", `/content/${type}`, { values }),
  contentUpdate: (type: string, id: number, values: Values) =>
    send<ContentItem>("PUT", `/content/${type}/${id}`, { values }),
  contentStatus: (type: string, id: number, status: ContentStatus) =>
    send<ContentItem>("POST", `/content/${type}/${id}/status`, { status }),
  contentDelete: (type: string, id: number) => send<void>("DELETE", `/content/${type}/${id}`),

  schedule: (kind: "daily" | "tips", start: string) => get<Schedule>(`/schedule/${kind}${query({ start, days: 35 })}`),
  setSchedule: (kind: "daily" | "tips", day: string, itemId: number | null) =>
    send<void>("PUT", `/schedule/${kind}/${day}`, { item_id: itemId }),

  users: (q: string, filter: string) => get<UserRow[]>(`/users${query({ q, filter })}`),
  user: (id: number) => get<UserDetail>(`/users/${id}`),
  block: (id: number, blocked: boolean, reason: string | null) =>
    send<UserDetail>("POST", `/users/${id}/block`, { blocked, reason }),
  nickname: (id: number, action: "hide" | "show" | "reset", reason: string | null) =>
    send<UserDetail>("POST", `/users/${id}/nickname`, { action, reason }),
  voidPoints: (id: number, entryIds: number[], reason: string) =>
    send<UserDetail>("POST", `/users/${id}/void`, { entry_ids: entryIds, reason }),

  openReports: () => get<ReportGroup[]>("/reports/open"),
  reportHistory: () => get<Report[]>("/reports"),
  resolve: (targetUserId: number, action: "dismiss" | "hide" | "reset" | "block", note: string | null) =>
    send<{ resolved: number }>("POST", "/reports/resolve", { target_user_id: targetUserId, action, note }),

  words: () => get<Word[]>("/words"),
  addWord: (word: string, kind: WordKind) => send<Word>("POST", "/words", { word, kind }),
  deleteWord: (id: number) => send<void>("DELETE", `/words/${id}`),

  stats: (days: number) => get<Stats>(`/stats${query({ days })}`),
  questionStats: () => get<QuestionStat[]>("/stats/questions"),
  flags: (days: number) => get<Flags>(`/stats/flags${query({ days })}`),
  audit: (beforeId?: number | null) => get<AuditPage>(`/audit${query({ before_id: beforeId })}`),

  admins: () => get<AdminRow[]>("/admins"),
  createAdmin: (body: {
    login: string;
    name: string;
    role: AdminRole;
    password: string;
    pickup_point_id?: number | null;
  }) => send<AdminRow>("POST", "/admins", body),
  updateAdmin: (
    id: number,
    body: { name?: string; role?: AdminRole; is_active?: boolean; pickup_point_id?: number | null },
  ) => send<AdminRow>("PATCH", `/admins/${id}`, body),
  reset2fa: (id: number) => send<AdminRow>("POST", `/admins/${id}/reset-2fa`),
  setAdminPassword: (id: number, password: string) =>
    send<AdminRow>("POST", `/admins/${id}/password`, { password }),

  marketCounts: () => get<MarketCounts>("/market/counts"),
  market: (filter: MarketFilter, q: string) => get<MarketRow[]>(`/market${query({ filter, q })}`),
  marketItem: (id: number) => get<MarketListing>(`/market/${id}`),
  approveListing: (id: number) => send<MarketListing>("POST", `/market/${id}/approve`),
  rejectListing: (id: number, body: MarketDecision) =>
    send<MarketListing>("POST", `/market/${id}/reject`, body),
  hideListing: (id: number, body: MarketDecision) =>
    send<MarketListing>("POST", `/market/${id}/hide`, body),
  dismissReports: (id: number) => send<MarketListing>("POST", `/market/${id}/dismiss-reports`),

  handoverPoints: () => get<HandoverPoint[]>("/handover/points"),
  handoverDesk: (pointId: number | null) => get<HandoverDesk>(`/handover${query({ point_id: pointId })}`),
  handoverLookup: (code: string, pointId: number | null) =>
    send<HandoverMatch>("POST", "/handover/lookup", { code, point_id: pointId }),
  handoverReceive: (requestId: number, code: string) =>
    send<HandoverItem>("POST", `/handover/${requestId}/receive`, { code }),
  handoverGive: (requestId: number, code: string) =>
    send<HandoverItem>("POST", `/handover/${requestId}/give`, { code }),
  handoverReturn: (listingId: number) =>
    send<{ ok: boolean }>("POST", `/handover/stored/${listingId}/return`),
};

/** Plain links: the browser sends the session cookie with these downloads. */
export const exportUrl = (kind: string, days: number) => `/api/admin/stats/export/${kind}?days=${days}`;
export const lessonPdfUrl = (id: number, lang: string) => `/api/admin/content/lessons/${id}/pdf?lang=${lang}`;

const MESSAGES: Record<string, string> = {
  invalid_credentials: "Login yoki parol noto'g'ri.",
  invalid_code: "Kod noto'g'ri. Ilovadagi yangi kodni kiriting.",
  code_expired: "Vaqt tugadi. Login va parolni qaytadan kiriting.",
  too_many_attempts: "Juda ko'p urinish. 15 daqiqadan keyin qayta urinib ko'ring.",
  admin_only: "Bu bo'lim faqat administratorlar uchun.",
  password_too_short: "Parol kamida 10 belgidan iborat bo'lsin.",
  password_too_long: "Parol juda uzun.",
  password_too_simple: "Parol juda oddiy: har xil belgilardan foydalaning.",
  wrong_password: "Joriy parol noto'g'ri.",
  login_taken: "Bu login band.",
  cannot_change_self: "O'z rolingizni o'zgartira yoki o'zingizni o'chira olmaysiz.",
  only_drafts: "Faqat qoralamani o'chirish mumkin. Boshqalarini arxivlang.",
  only_published: "Jadvalga faqat nashr qilingan kontentni qo'yish mumkin.",
  nothing_to_void: "Bekor qilinadigan yozuv qolmagan.",
  word_exists: "Bu so'z ro'yxatda bor.",
  bad_transition: "Bu holatga to'g'ridan-to'g'ri o'tkazib bo'lmaydi.",
  publish_blocked: "Nashr qilib bo'lmaydi: quyidagi xatolarni tuzating.",
  invalid: "Ba'zi maydonlar noto'g'ri to'ldirilgan.",
  bad_origin: "So'rov rad etildi (boshqa saytdan).",
  in_use: "O'chirib bo'lmaydi: bu yozuv ishlatilmoqda. Arxivlang.",
  point_required: "Topshirish joyini tanlang.",
  code_not_found: "Bu kod bilan kutilayotgan buyum topilmadi. Raqamlarni tekshiring.",
  wrong_code: "Kod mos kelmadi.",
  too_many_lookups: "Juda ko'p urinish. Bir daqiqadan keyin qayta urinib ko'ring.",
  listing_not_found: "E'lon topilmadi.",
};

export function errorText(error: unknown): string {
  if (error instanceof AdminApiError) {
    const detail = error.detail as { code?: string } | string;
    const code = typeof detail === "string" ? detail : detail?.code;
    if (code && MESSAGES[code]) return MESSAGES[code];
    if (error.status === 401) return "Sessiya tugadi. Qaytadan kiring.";
    if (error.status >= 500) return "Serverda xatolik. Birozdan keyin qayta urinib ko'ring.";
    return `Xatolik (${code ?? error.status}).`;
  }
  return "Server bilan aloqa yo'q. Internetni tekshiring.";
}
