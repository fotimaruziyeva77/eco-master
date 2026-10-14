import { Check, ChevronRight, GraduationCap } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api, ApiError, type Daily, type Home, type HomeClassTask } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { Emoji } from "../components/Emoji";
import { LevelProgress } from "../components/LevelProgress";
import { PROJECT_POINTS } from "../components/ProjectCard";
import { tint, TopBar } from "../components/ui";
import { VideoRow } from "../components/VideoRow";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";
import { enqueue } from "../outbox";
import { useCelebrate } from "../state/celebration";
import { useUser } from "../state/user";
import { haptic } from "../telegram";
import { useDue } from "./classes/parts";

/** Days in a row for the weekly bonus (the server's STREAK_BONUS_EVERY). */
const STREAK_DAYS = 7;

/**
 * Home: today's task first, then two games, a project and the waste types. Pictures and
 * numbers instead of explanations: the user should see what to do without reading.
 */
export function HomeScreen() {
  const { t } = useTranslation();
  const { user, setUser } = useUser();
  const home = useLoad(() => api.home(), []);
  const [daily, setDaily] = useState<Daily | null>(null);

  // The home payload carries fresh points and streak; keep the shared user in sync.
  useEffect(() => {
    if (!home.data) return;
    setUser(home.data.user);
    setDaily(home.data.daily);
  }, [home.data, setUser]);

  const data = home.data;
  return (
    <main className="screen screen--with-nav">
      <TopBar />
      <h1 className="greeting">{t("home.greeting", { name: user.nickname })}</h1>

      <div className="stack stack--lg">
        {user.path === "teacher" && <TeacherCard />}
        {home.loading && !data && <InlineLoading />}
        {home.error !== undefined && !data && <InlineError error={home.error} onRetry={home.reload} />}
        {daily?.task && <DailyTaskCard daily={daily} onChange={setDaily} />}
        {data?.class_task && <ClassTaskCard task={data.class_task} />}
        {data && data.videos.length > 0 && <VideoRow videos={data.videos} />}
        <PlayTiles />
        <LevelProgress user={user} />
        {/* Without videos yet: one project to try instead. */}
        {data?.featured && data.videos.length === 0 && (
          <FeaturedProject project={data.featured} categories={data.categories} />
        )}
        {data && <Categories categories={data.categories} />}
        {data?.tip && <Tip text={data.tip.text} />}
      </div>
    </main>
  );
}

/** On the teacher path the lessons are one tap away (TZ 8.9). */
function TeacherCard() {
  const { t } = useTranslation();
  return (
    <Link className="list-row teacher-card" to="/teachers">
      <span className="icon-tile icon-tile--sky" aria-hidden="true">
        <GraduationCap size={22} />
      </span>
      <span className="list-row__text">
        <strong>{t("home.teacherTitle")}</strong>
      </span>
      <ChevronRight className="list-row__chevron" size={20} />
    </Link>
  );
}

/** Seven dots for the days in a row towards the weekly bonus. */
function StreakDots({ streak, bonus }: { streak: number; bonus: number }) {
  const { t } = useTranslation();
  const filled = streak === 0 ? 0 : ((streak - 1) % STREAK_DAYS) + 1;
  return (
    <span className="streak-dots" role="img" aria-label={t("home.streakDots", { count: streak, points: bonus })}>
      {Array.from({ length: STREAK_DAYS }, (_, i) => (
        <span key={i} className={i < filled ? "streak-dot is-on" : "streak-dot"} />
      ))}
      <span className="streak-dots__bonus" aria-hidden="true">
        <Emoji char="🎁" />+{bonus}
      </span>
    </span>
  );
}

function DailyTaskCard({ daily, onChange }: { daily: Daily; onChange: (d: Daily) => void }) {
  const { t } = useTranslation();
  const tr = useTr();
  const { user, setUser } = useUser();
  const celebrate = useCelebrate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(false);
  const [savedOffline, setSavedOffline] = useState(false);
  // One id per task: a retried request after a network error is written only once.
  const eventId = useMemo(() => crypto.randomUUID(), [daily.task?.id]);
  const task = daily.task!;

  async function markDone() {
    setSaving(true);
    setError(false);
    try {
      const result = await api.dailyDone(eventId);
      haptic.success();
      onChange({
        ...daily,
        done_today: true,
        streak_current: result.streak_current,
        streak_best: result.streak_best,
        days_to_bonus: STREAK_DAYS - (result.streak_current % STREAK_DAYS),
      });
      setUser({
        ...user,
        points_total: result.points_total,
        streak_current: result.streak_current,
        streak_best: result.streak_best,
        done_today: true,
      });
      celebrate(result.new_badges ?? []);
    } catch (failure) {
      if (!(failure instanceof ApiError)) {
        // No connection: done for today on this device, sent with the same id later (QM-18).
        enqueue({ id: eventId, kind: "daily_done" });
        onChange({ ...daily, done_today: true });
        setSavedOffline(true);
        return;
      }
      haptic.error();
      setError(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="card card--hero task-card">
      <div className="task-card__head">
        <span className="task-card__label">{t("home.taskTitle")}</span>
        <span className="task-card__points">
          <Emoji char="⭐" /> +{task.points}
        </span>
      </div>
      <p className="task-card__text">{tr(task.text)}</p>
      {error && <p className="small">{t("project.doneError")}</p>}
      {savedOffline && <p className="small">{t("network.savedOffline")}</p>}
      <div className="task-card__foot">
        <StreakDots streak={daily.streak_current} bonus={daily.bonus_points} />
        {daily.done_today ? (
          <span className="task-card__done">
            <Check size={18} /> {t("home.taskDone")}
          </span>
        ) : (
          <button type="button" className="btn btn--white" disabled={saving} onClick={() => void markDone()}>
            {t("project.done")} <Check size={18} />
          </button>
        )}
      </div>
    </section>
  );
}

/** A project the pupil's teacher gave the class (stage 5), until it is done. */
function ClassTaskCard({ task }: { task: HomeClassTask }) {
  const { t } = useTranslation();
  const tr = useTr();
  const due = useDue();
  return (
    <Link className="list-row class-task" to={`/projects/${task.project_slug}`}>
      <span className="icon-tile icon-tile--sky" aria-hidden="true">
        <Emoji char={task.icon} />
      </span>
      <span className="list-row__text">
        <span className="hint small strong">
          <Emoji char="🏫" /> {t("home.classTask", { name: task.class_name })}
        </span>
        <strong>{tr(task.title)}</strong>
        <span className="hint small">{due(task.due_date)}</span>
      </span>
      <ChevronRight className="list-row__chevron" size={20} />
    </Link>
  );
}

function PlayTiles() {
  const { t } = useTranslation();
  return (
    <div className="play-grid">
      <Link className="play-tile play-tile--sky" to="/games/sort">
        <Emoji char="♻️" />
        <strong>{t("home.game")}</strong>
      </Link>
      <Link className="play-tile play-tile--amber" to="/games/quiz">
        <Emoji char="🧠" />
        <strong>{t("home.quiz")}</strong>
      </Link>
    </div>
  );
}

function FeaturedProject({
  project,
  categories,
}: {
  project: NonNullable<Home["featured"]>;
  categories: Home["categories"];
}) {
  const { t } = useTranslation();
  const tr = useTr();
  const category = categories.find((c) => c.code === project.category_code);
  return (
    <Link className="card featured" to={`/projects/${project.slug}`}>
      <div className="featured__media">
        {project.poster_url ? (
          <img src={project.poster_url} alt="" loading="lazy" />
        ) : (
          <Emoji char={category?.icon ?? "♻️"} />
        )}
        <span className="featured__badge">{t("home.makeIt")}</span>
      </div>
      <div className="featured__body">
        <h3>{tr(project.title)}</h3>
        <div className="chips">
          <span className="chip chip--neutral chip--sm">
            <Emoji char="⏱️" /> {t("common.minutes", { count: project.duration_min })}
          </span>
          <span className="chip chip--amber chip--sm">
            <Emoji char="⭐" /> +{PROJECT_POINTS}
          </span>
        </div>
      </div>
    </Link>
  );
}

function Categories({ categories }: { categories: Home["categories"] }) {
  const { t } = useTranslation();
  const tr = useTr();
  const withProjects = categories.filter((c) => c.project_count > 0);
  if (withProjects.length === 0) return null;
  return (
    <section className="stack">
      <h2>{t("home.wasteTypes")}</h2>
      <div className="chip-scroll">
        {withProjects.map((c) => (
          <Link key={c.code} className="category-chip" to={`/learn/${c.code}`} style={tint(c.color)}>
            <span className="category-chip__icon" aria-hidden="true">
              <Emoji char={c.icon} />
            </span>
            <strong>{tr(c.name)}</strong>
          </Link>
        ))}
      </div>
    </section>
  );
}

/** Tip of the day: two lines; a tap shows all of it. */
function Tip({ text }: { text: NonNullable<Home["tip"]>["text"] }) {
  const { t } = useTranslation();
  const tr = useTr();
  const [open, setOpen] = useState(false);
  return (
    <button type="button" className="card card--soft tip-card" aria-expanded={open} onClick={() => setOpen(!open)}>
      <Emoji char="💡" />
      <span>
        <strong>{t("home.tipTitle")}</strong>
        <span className={open ? "tip-card__text" : "tip-card__text is-clamped"}>{tr(text)}</span>
      </span>
    </button>
  );
}
