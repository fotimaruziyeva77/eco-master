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
export type Badge = Schemas["BadgeOut"];
export type GamesOverview = Schemas["GamesOut"];
export type QuizRound = Schemas["QuizRoundOut"];
export type QuizQuestion = Schemas["QuizQuestionOut"];
export type QuizAnswer = Schemas["QuizAnswerOut"];
export type GameRound = Schemas["GameRoundOut"];
export type GameItem = Schemas["GameItemOut"];
export type GameAnswer = Schemas["GameAnswerOut"];
export type Daily = Schemas["DailyOut"];
export type DailyDone = Schemas["DailyDoneOut"];
export type Leaderboard = Schemas["LeaderboardOut"];
export type LeaderboardEntry = Schemas["LeaderboardEntryOut"];
export type Stats = Schemas["StatsOut"];
export type Period = Leaderboard["period"];
export type LessonSummary = Schemas["LessonSummaryOut"];
export type Lesson = Schemas["LessonOut"];
export type ShareKind = Schemas["ShareIn"]["kind"];
export type ShareResult = Schemas["ShareOut"];
export type StoryShare = Schemas["StoryOut"];
export type ListingCard = Schemas["ListingCardOut"];
export type ListingPage = Schemas["ListingPageOut"];
export type Listing = Schemas["ListingOut"];
export type ListingInput = Schemas["ListingIn"];
export type ListingKind = Listing["kind"];
export type ListingStatus = Listing["status"];
export type RequestStatus = Schemas["ListingRequestOut"]["status"];
export type MyListing = Schemas["MyListingOut"];
export type MyRequest = Schemas["MyRequestOut"];
export type PickupPoint = Schemas["PickupPointOut"];
export type Photo = Schemas["PhotoOut"];
export type ReportReason = Schemas["ListingReportIn"]["reason"];
export type SchoolClass = Schemas["ClassOut"];
export type ClassDetail = Schemas["ClassDetailOut"];
export type ClassMember = Schemas["ClassMemberOut"];
export type ClassTask = Schemas["ClassTaskOut"];
export type ClassPreview = Schemas["ClassPreviewOut"];
export type MyClass = Schemas["MyClassOut"];
export type RankedMember = Schemas["RankedMemberOut"];
export type League = Schemas["LeagueOut"];
export type HomeClassTask = Schemas["HomeClassTaskOut"];
export type AvatarChoice = Schemas["AvatarOut"];

/** One language of a lesson body (TZ 8.9); the API types it as a free-form object. */
export type LessonBody = {
  goal: string;
  materials: string[];
  plan: { minutes: number; title: string; text: string }[];
  questions: string[];
  homework: string;
  app_task: string;
};

let sessionToken: string | null = null;

export const hasSession = () => sessionToken !== null;

// Whether the last request reached the server; the offline banner listens to this.
let reachable = true;
const reachability = new EventTarget();

export const isReachable = () => reachable;

export function onReachabilityChange(listener: () => void): () => void {
  reachability.addEventListener("change", listener);
  return () => reachability.removeEventListener("change", listener);
}

function setReachable(value: boolean): void {
  if (reachable === value) return;
  reachable = value;
  reachability.dispatchEvent(new Event("change"));
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super(code);
  }
}

async function send(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (sessionToken) headers.set("Authorization", `Bearer ${sessionToken}`);

  let response: Response;
  try {
    response = await fetch(`/api${path}`, { ...init, headers });
  } catch (error) {
    setReachable(false); // no connection: a TypeError, not an ApiError
    throw error;
  }
  setReachable(true);
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
  return response;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await send(path, init);
  if (response.status === 204) return undefined as T;
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
  health: () => request<{ status: string }>("/health"),
  me: () => request<User>("/me"),
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
  projects: () => request<ProjectSummary[]>("/projects"),
  cards: () => request<CardSummary[]>("/cards"),
  card: (slug: string) => request<CardDetail>(`/cards/${encodeURIComponent(slug)}`),

  myBadges: () => request<Badge[]>("/me/badges"),
  games: () => request<GamesOverview>("/games"),
  quizRound: (category: string | null) => post<QuizRound>("/quiz/rounds", { category }),
  quizAnswer: (roundToken: string, questionId: number, optionIndex: number) =>
    post<QuizAnswer>("/quiz/answer", {
      round_token: roundToken,
      question_id: questionId,
      option_index: optionIndex,
    }),
  gameRound: () => post<GameRound>("/game/rounds"),
  gameAnswer: (roundToken: string, itemId: number, bin: string | null, quick: boolean) =>
    post<GameAnswer>("/game/answer", { round_token: roundToken, item_id: itemId, bin, quick }),

  daily: () => request<Daily>("/daily"),
  dailyDone: (clientEventId: string) =>
    post<DailyDone>("/daily/done", { client_event_id: clientEventId }),
  leaderboard: (period: Period) => request<Leaderboard>(`/leaderboard?period=${period}`),
  league: () => request<League>("/league"),
  report: (targetUserId: number) => post<{ ok: boolean }>("/reports", { target_user_id: targetUserId }),
  myStats: () => request<Stats>("/me/stats"),
  changeNickname: (nickname: string) => post<User>("/me/nickname", { nickname }),
  myAvatars: () => request<AvatarChoice[]>("/me/avatars"),
  setAvatar: (avatar: string | null) => post<User>("/me/avatar", { avatar }),
  deleteMe: () => request<void>("/me", { method: "DELETE" }),

  lessons: () => request<LessonSummary[]>("/lessons"),
  lesson: (slug: string) => request<Lesson>(`/lessons/${encodeURIComponent(slug)}`),
  lessonPdf: (slug: string, language: Language) =>
    send(`/lessons/${encodeURIComponent(slug)}/pdf?lang=${language}`).then((r) => r.blob()),
  sendLesson: (slug: string, language: Language) =>
    post<{ sent: boolean }>(`/lessons/${encodeURIComponent(slug)}/send`, { language }),
  share: (kind: ShareKind, objectId?: string) =>
    post<ShareResult>("/share", { kind, object_id: objectId ?? null }),
  shareStory: () => post<StoryShare>("/share/story", {}),
  events: (events: Schemas["EventsIn"]["events"]) => post<void>("/events", { events }),

  market: (params: { kind?: ListingKind | null; point?: number | null; offset?: number }) => {
    const q = new URLSearchParams();
    if (params.kind) q.set("kind", params.kind);
    if (params.point) q.set("point", String(params.point));
    if (params.offset) q.set("offset", String(params.offset));
    return request<ListingPage>(`/market?${q}`);
  },
  marketPoints: () => request<PickupPoint[]>("/market/points"),
  listing: (id: number) => request<Listing>(`/market/${id}`),
  myListings: () => request<MyListing[]>("/market/mine"),
  myRequests: () => request<MyRequest[]>("/market/requests"),
  /** One photo, already resized on the phone; the server re-encodes it without metadata. */
  uploadPhoto: (photo: Blob) =>
    send("/market/photos", {
      method: "POST",
      body: photo,
      headers: { "Content-Type": photo.type || "image/jpeg" },
    }).then((r) => r.json() as Promise<Photo>),
  createListing: (body: ListingInput) => post<Listing>("/market", body),
  updateListing: (id: number, body: ListingInput) =>
    request<Listing>(`/market/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteListing: (id: number) => request<void>(`/market/${id}`, { method: "DELETE" }),
  like: (id: number) => post<Schemas["LikeOut"]>(`/market/${id}/like`),
  unlike: (id: number) => request<Schemas["LikeOut"]>(`/market/${id}/like`, { method: "DELETE" }),
  reportListing: (id: number, reason: ReportReason) => post<{ ok: boolean }>(`/market/${id}/report`, { reason }),
  askFor: (id: number) => post<Listing>(`/market/${id}/request`),
  withdrawRequest: (id: number) => request<Listing>(`/market/${id}/request`, { method: "DELETE" }),
  acceptRequest: (requestId: number) => post<Listing>(`/market/requests/${requestId}/accept`),
  declineRequest: (requestId: number) => post<Listing>(`/market/requests/${requestId}/decline`),
  cancelHandover: (id: number) => post<Listing>(`/market/${id}/cancel`),

  // A teacher's classes.
  classes: () => request<SchoolClass[]>("/classes"),
  createClass: (name: string) => post<SchoolClass>("/classes", { name }),
  classDetail: (id: number) => request<ClassDetail>(`/classes/${id}`),
  renameClass: (id: number, name: string) =>
    request<SchoolClass>(`/classes/${id}`, { method: "PATCH", body: JSON.stringify({ name }) }),
  deleteClass: (id: number) => request<void>(`/classes/${id}`, { method: "DELETE" }),
  removeMember: (id: number, userId: number) =>
    request<void>(`/classes/${id}/members/${userId}`, { method: "DELETE" }),
  addClassTask: (id: number, projectSlug: string, dueDate: string) =>
    post<ClassTask>(`/classes/${id}/tasks`, { project_slug: projectSlug, due_date: dueDate }),
  deleteClassTask: (id: number, taskId: number) =>
    request<void>(`/classes/${id}/tasks/${taskId}`, { method: "DELETE" }),
  // A pupil's class.
  previewClass: (code: string) => request<ClassPreview>(`/classes/preview/${encodeURIComponent(code)}`),
  joinClass: (code: string) => post<MyClass>("/classes/join", { code }),
  myClass: () => request<MyClass | null>("/my-class"),
  leaveClass: () => request<void>("/my-class", { method: "DELETE" }),
};
