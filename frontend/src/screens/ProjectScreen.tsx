import { Check, ListChecks, PartyPopper, ShieldAlert, ShieldCheck, Waypoints } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { PROJECT_POINTS, SAFETY_ICON } from "../components/ProjectCard";
import { SubpageHeader } from "../components/ui";
import { VideoPlayer } from "../components/VideoPlayer";
import { useBack } from "../hooks/useBack";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";
import { useCelebrate } from "../state/celebration";
import { useUser } from "../state/user";
import { haptic } from "../telegram";

/** "I did it" unlocks after the video ends or this many seconds on the page (TZ 8.3). */
const UNLOCK_SECONDS = 30;

export function ProjectScreen() {
  const { slug = "" } = useParams();
  const { t } = useTranslation();
  const tr = useTr();
  const { user, setUser } = useUser();
  const celebrate = useCelebrate();
  const data = useLoad(() => api.project(slug), [slug]);
  const project = data.data;
  const back = useBack(project ? `/learn/${project.category_code}` : "/learn");

  const [secondsLeft, setSecondsLeft] = useState(UNLOCK_SECONDS);
  const [videoEnded, setVideoEnded] = useState(false);
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);
  const [checked, setChecked] = useState<Set<number>>(new Set());
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  // One id per visit: a retried request after a network error cannot add points twice.
  const eventId = useMemo(() => crypto.randomUUID(), [slug]);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = window.setTimeout(() => setSecondsLeft((s) => s - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [secondsLeft]);

  const isDone = done || Boolean(project?.done);
  const unlocked = videoEnded || secondsLeft <= 0;
  const materials = tr<string[]>(project?.materials) ?? [];
  const steps = tr<string[]>(project?.steps) ?? [];

  async function markDone() {
    if (!project || saving) return;
    setSaving(true);
    setMessage(null);
    try {
      const result = await api.projectDone(project.slug, eventId);
      setDone(true);
      setUser({ ...user, points_total: result.points_total });
      haptic.success();
      if (result.awarded) setMessage({ kind: "ok", text: t("project.earned", { count: result.points }) });
      celebrate(result.new_badges ?? []);
    } catch {
      haptic.error();
      setMessage({ kind: "error", text: t("project.doneError") });
    } finally {
      setSaving(false);
    }
  }

  function toggle(i: number) {
    haptic.tap();
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  return (
    <main className="screen screen--with-action">
      <SubpageHeader onBack={back} title={t("project.title")} />
      {data.loading && !project && <InlineLoading />}
      {data.error !== undefined && !project && <InlineError error={data.error} onRetry={data.reload} />}

      {project && (
        <article className="stack stack--lg">
          <div className="stack">
            <span className="chip" style={{ alignSelf: "flex-start" }}>
              {project.category_icon} {t("project.categoryProject", { name: tr(project.category_name) })}
            </span>
            <h1>{tr(project.title)}</h1>
            <div className="chips">
              <span className="chip chip--neutral">
                {SAFETY_ICON[project.safety_level]} {t(`project.difficulty.${project.difficulty}`)} —{" "}
                {t(`project.safety.${project.safety_level}`)}
              </span>
              <span className="chip chip--neutral">⏱ {t("common.minutes", { count: project.duration_min })}</span>
              <span className="chip chip--amber">⭐ +{t("home.points", { count: PROJECT_POINTS })}</span>
            </div>
            {project.done_count > 0 && (
              <span className="hint small">{t("project.doneCount", { count: project.done_count })}</span>
            )}
          </div>

          <VideoPlayer
            url={project.video_url}
            poster={project.poster_url}
            icon={project.category_icon}
            onEnded={() => setVideoEnded(true)}
          />

          {project.safety_text && (
            <section className={`safety safety--${project.safety_level}`} role="note">
              <span className="icon-tile" aria-hidden="true">
                {project.safety_level === "green" ? <ShieldCheck size={22} /> : <ShieldAlert size={22} />}
              </span>
              <div>
                <h3>{t("project.safetyTitle")}</h3>
                <p className="text-2">{tr(project.safety_text)}</p>
              </div>
            </section>
          )}

          <section className="card">
            <div className="row row--between">
              <h3 className="row">
                <ListChecks size={20} aria-hidden="true" /> {t("project.materials")}
              </h3>
              <span className="chip chip--sm">
                {t("project.ready", { done: checked.size, total: materials.length })}
              </span>
            </div>
            <ul className="checklist">
              {materials.map((item, i) => (
                <li key={item}>
                  <button type="button" role="checkbox" aria-checked={checked.has(i)} onClick={() => toggle(i)}>
                    <span className="checklist__box" aria-hidden="true">
                      <Check size={14} />
                    </span>
                    <span>{item}</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section className="stack">
            <h3 className="row">
              <Waypoints size={20} aria-hidden="true" /> {t("project.steps")}
            </h3>
            {steps.map((step, i) => (
              <div key={step} className="card step-card">
                <span className="step-card__num">{i + 1}</span>
                <p>{step}</p>
              </div>
            ))}
          </section>
        </article>
      )}

      {project && (
        <div className="action-bar">
          {message && (
            <p className={message.kind === "ok" ? "toast" : "toast toast--error"} role="status">
              {message.text}
            </p>
          )}
          <button
            type="button"
            className="btn btn--block"
            disabled={isDone || !unlocked || saving}
            onClick={() => void markDone()}
          >
            <PartyPopper size={20} aria-hidden="true" />
            {isDone
              ? t("project.alreadyDone")
              : unlocked
                ? t("project.doneCta", { count: PROJECT_POINTS })
                : t("project.doneWait", { count: secondsLeft })}
          </button>
        </div>
      )}
    </main>
  );
}
