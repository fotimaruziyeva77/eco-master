import { Check, Play, ShieldAlert, ShieldCheck } from "lucide-react";
import { useEffect, useMemo, useState, type CSSProperties } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router";

import { api, ApiError } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { Emoji } from "../components/Emoji";
import { PROJECT_POINTS } from "../components/ProjectCard";
import { ShareButton } from "../components/ShareButton";
import { SubpageHeader } from "../components/ui";
import { VideoPlayer } from "../components/VideoPlayer";
import { useBack } from "../hooks/useBack";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";
import { trackVideo } from "../analytics";
import { enqueue } from "../outbox";
import { useCelebrate } from "../state/celebration";
import { stepTimes, stepsWatched } from "../steps";
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
  const navigate = useNavigate();

  const [secondsLeft, setSecondsLeft] = useState(UNLOCK_SECONDS);
  // Going through the steps to the end counts like watching the whole video.
  const [videoEnded, setVideoEnded] = useState(() => stepsWatched.has(slug));
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
  const times = stepTimes(project, steps.length);
  const pictures = project?.step_pictures ?? [];

  function openSteps(step: number) {
    haptic.tap();
    navigate(`/projects/${slug}/steps`, { state: { project, step } });
  }

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
    } catch (error) {
      if (!(error instanceof ApiError)) {
        // No connection: keep it on the device and send it later with the same id (QM-18).
        enqueue({ id: eventId, kind: "project_done", slug: project.slug });
        setDone(true);
        setMessage({ kind: "ok", text: t("network.savedOffline") });
        return;
      }
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

  // The button fills up while it waits: no countdown to read.
  const waited = { "--progress": `${Math.round(((UNLOCK_SECONDS - secondsLeft) / UNLOCK_SECONDS) * 100)}%` } as CSSProperties;

  return (
    <main className="screen screen--with-action">
      <SubpageHeader onBack={back} title={project ? tr(project.category_name) : t("project.title")} />
      {data.loading && !project && <InlineLoading />}
      {data.error !== undefined && !project && <InlineError error={data.error} onRetry={data.reload} />}

      {project && (
        <article className="stack stack--lg">
          <div className="stack">
            <h1>{tr(project.title)}</h1>
            <div className="chips">
              <span className="chip chip--neutral chip--sm">{t(`project.difficulty.${project.difficulty}`)}</span>
              <span className="chip chip--neutral chip--sm">
                <Emoji char="⏱️" /> {t("common.minutes", { count: project.duration_min })}
              </span>
              <span className="chip chip--amber chip--sm">
                <Emoji char="⭐" /> +{PROJECT_POINTS}
              </span>
              {project.done_count > 0 && (
                <span className="chip chip--sm" title={t("project.doneCount", { count: project.done_count })}>
                  <Emoji char="🙌" /> {project.done_count}
                </span>
              )}
              {isDone && (
                <span className="chip chip--sm">
                  <Check size={14} /> {t("project.alreadyDone")}
                </span>
              )}
            </div>
          </div>

          <VideoPlayer
            url={project.video_url}
            poster={project.poster_url}
            icon={project.category_icon}
            onPlay={() => trackVideo("video_play", project.slug)}
            onEnded={() => {
              setVideoEnded(true);
              trackVideo("video_complete", project.slug);
            }}
          />

          {project.safety_text && (
            <section className={`safety safety--${project.safety_level}`} role="note">
              <span className="icon-tile" aria-hidden="true">
                {project.safety_level === "green" ? <ShieldCheck size={22} /> : <ShieldAlert size={22} />}
              </span>
              <div>
                <h3>{t(`project.safety.${project.safety_level}`)}</h3>
                <p className="text-2">{tr(project.safety_text)}</p>
              </div>
            </section>
          )}

          <section className="card">
            <div className="row row--between">
              <h3>{t("project.materials")}</h3>
              <span className="chip chip--sm">
                {checked.size}/{materials.length}
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
            <div className="row row--between">
              <h3>{t("project.steps")}</h3>
              {times && (
                <button type="button" className="btn btn--soft btn--sm" onClick={() => openSteps(0)}>
                  <Play size={16} fill="currentColor" aria-hidden="true" /> {t("project.stepByStep")}
                </button>
              )}
            </div>
            {steps.map((step, i) =>
              times ? (
                // Each step opens its own part of the video.
                <button key={step} type="button" className="card step-card step-card--clip" onClick={() => openSteps(i)}>
                  <span className="step-card__picture" aria-hidden="true">
                    {pictures[i] && <img src={pictures[i] ?? undefined} alt="" loading="lazy" />}
                    <span className="step-card__num">{i + 1}</span>
                  </span>
                  <p>{step}</p>
                  <Play size={16} fill="currentColor" className="step-card__play" aria-hidden="true" />
                </button>
              ) : (
                <div key={step} className="card step-card">
                  <span className="step-card__num">{i + 1}</span>
                  <p>{step}</p>
                </div>
              ),
            )}
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
          {isDone ? (
            <ShareButton kind="project" objectId={project.slug} label={t("share.project")} className="btn btn--block" />
          ) : (
            <button
              type="button"
              className={unlocked ? "btn btn--block" : "btn btn--block btn--waiting"}
              style={unlocked ? undefined : waited}
              disabled={!unlocked || saving}
              aria-label={unlocked ? undefined : t("project.doneWait", { count: secondsLeft })}
              onClick={() => void markDone()}
            >
              <Emoji char="🎉" /> {t("project.done")}
              <span className="btn__points">
                <Emoji char="⭐" /> +{PROJECT_POINTS}
              </span>
            </button>
          )}
        </div>
      )}
    </main>
  );
}
