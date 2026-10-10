import { AlarmClock, Check, ChevronRight, ClipboardList, GraduationCap, Lightbulb } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api, type Daily, type Home } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { LevelProgress } from "../components/LevelProgress";
import { PROJECT_POINTS, SAFETY_ICON } from "../components/ProjectCard";
import { tint, TopBar } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";
import { useCelebrate } from "../state/celebration";
import { useUser } from "../state/user";
import { haptic } from "../telegram";

export function HomeScreen() {
  const { t } = useTranslation();
  const tr = useTr();
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
      <TopBar subtitle={t("nav.home")} />
      <div className="greeting">
        <div>
          <h1>{t("home.greeting", { name: user.nickname })} 🌱</h1>
          <p className="hint">{t("home.subtitle")}</p>
        </div>
        {user.path && <span className="chip">{t(`roles.${user.path}`)}</span>}
      </div>

      <div className="stack stack--lg">
        <LevelProgress user={user} />
        {user.path === "teacher" && <TeacherCard />}
        {home.loading && !data && <InlineLoading />}
        {home.error !== undefined && !data && <InlineError error={home.error} onRetry={home.reload} />}
        {daily && <StreakBanner daily={daily} />}
        {daily?.task && <DailyTaskCard daily={daily} onChange={setDaily} />}
        {data?.tip && (
          <section className="card card--soft tip-card">
            <span className="icon-tile icon-tile--amber" aria-hidden="true">
              <Lightbulb size={22} />
            </span>
            <div>
              <h3>{t("home.tipTitle")}</h3>
              <p className="text-2">{tr(data.tip.text)}</p>
            </div>
          </section>
        )}
        <QuickGames />
        {data && <Categories categories={data.categories} />}
        {data?.featured && <FeaturedProject project={data.featured} categories={data.categories} />}
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
        <span className="hint small">{t("home.teacherText")}</span>
      </span>
      <ChevronRight className="list-row__chevron" size={20} />
    </Link>
  );
}

function StreakBanner({ daily }: { daily: Daily }) {
  const { t } = useTranslation();
  const active = daily.streak_current > 0;
  return (
    <section className="card card--amber streak-banner">
      <span className="flame" aria-hidden="true">
        🔥
      </span>
      <div>
        <strong>
          {active ? t("home.streakTitle", { count: daily.streak_current }) : t("home.streakStart")}
        </strong>
        <span className="small text-2">
          {active
            ? t("home.streakBonus", { points: daily.bonus_points, count: daily.days_to_bonus })
            : t("home.streakStartHint")}
        </span>
      </div>
    </section>
  );
}

function DailyTaskCard({ daily, onChange }: { daily: Daily; onChange: (d: Daily) => void }) {
  const { t } = useTranslation();
  const tr = useTr();
  const { user, setUser } = useUser();
  const celebrate = useCelebrate();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(false);
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
        days_to_bonus: 7 - (result.streak_current % 7),
      });
      setUser({
        ...user,
        points_total: result.points_total,
        streak_current: result.streak_current,
        streak_best: result.streak_best,
        done_today: true,
      });
      celebrate(result.new_badges ?? []);
    } catch {
      haptic.error();
      setError(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="card card--hero">
      <div className="task-card__head">
        <span className="task-card__label">
          <ClipboardList size={15} /> {t("home.taskTitle")}
        </span>
        <span className="task-card__points">⭐ +{t("home.points", { count: task.points })}</span>
      </div>
      <p className="task-card__text">{tr(task.text)}</p>
      {error && <p className="small">{t("project.doneError")}</p>}
      <div className="task-card__foot">
        <span className="task-card__deadline">
          <AlarmClock size={16} /> {t("home.taskDeadline")}
        </span>
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

function QuickGames() {
  const { t } = useTranslation();
  return (
    <section>
      <div className="section-head">
        <h2>{t("home.quickGames")}</h2>
        <Link to="/games" className="ok-text small">
          {t("home.all")}
        </Link>
      </div>
      <div className="quick-grid">
        <Link className="game-tile" to="/games/sort">
          <span className="icon-tile icon-tile--sky" aria-hidden="true">
            ♻️
          </span>
          <span className="chip chip--sm">{t("home.sortChip")}</span>
          <strong>{t("home.game")}</strong>
          <span className="hint small">{t("home.sortHint")}</span>
        </Link>
        <Link className="game-tile" to="/games/quiz">
          <span className="icon-tile icon-tile--amber" aria-hidden="true">
            🧠
          </span>
          <span className="chip chip--sm chip--amber">{t("home.quizChip")}</span>
          <strong>{t("home.quiz")}</strong>
          <span className="hint small">{t("home.quizHint")}</span>
        </Link>
      </div>
    </section>
  );
}

function Categories({ categories }: { categories: Home["categories"] }) {
  const { t } = useTranslation();
  const tr = useTr();
  return (
    <section>
      <div className="section-head">
        <div>
          <h2>{t("home.wasteTypes")}</h2>
          <p className="hint small">{t("home.wasteTypesHint")}</p>
        </div>
      </div>
      <div className="chip-scroll">
        {categories.map((c) => (
          <Link key={c.code} className="category-chip" to={`/learn/${c.code}`} style={tint(c.color)}>
            <span className="category-chip__icon" aria-hidden="true">
              {c.icon}
            </span>
            <span>
              <strong>{tr(c.name)}</strong>
              <small>{t("learn.projects", { count: c.project_count })}</small>
            </span>
          </Link>
        ))}
      </div>
    </section>
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
    <section className="card featured">
      <div className="featured__media">
        {project.poster_url ? (
          <img src={project.poster_url} alt="" loading="lazy" />
        ) : (
          <span aria-hidden="true">{category?.icon ?? "♻️"}</span>
        )}
        <span className="chip chip--neutral featured__badge">
          {SAFETY_ICON[project.safety_level]} {t(`project.safetyShort.${project.safety_level}`)}
        </span>
        <span className="featured__time">⏱ {t("common.minutes", { count: project.duration_min })}</span>
      </div>
      <div className="featured__body stack">
        <span className="featured__meta">
          {category ? tr(category.name) : ""} DIY · +{t("home.points", { count: PROJECT_POINTS })}
        </span>
        <h3>{tr(project.title)}</h3>
        <div className="row row--between">
          <span className="hint small">{t(`project.difficulty.${project.difficulty}`)}</span>
          <Link className="btn btn--soft btn--sm" to={`/projects/${project.slug}`}>
            {t("home.start")} <ChevronRight size={16} />
          </Link>
        </div>
      </div>
    </section>
  );
}
