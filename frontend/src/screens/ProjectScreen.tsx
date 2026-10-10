import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading, SubpageHeader } from "../components/common";
import { SAFETY_ICON } from "../components/ProjectCard";
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

  return (
    <main className="screen screen--with-action">
      <SubpageHeader onBack={back} />
      {data.loading && !project && <InlineLoading />}
      {data.error !== undefined && !project && <InlineError error={data.error} onRetry={data.reload} />}

      {project && (
        <article className="project">
          <h1>{tr(project.title)}</h1>
          <div className="chips">
            <span className="chip">{t(`project.difficulty.${project.difficulty}`)}</span>
            <span className="chip">⏱ {t("common.minutes", { count: project.duration_min })}</span>
            <span className="chip">
              {SAFETY_ICON[project.safety_level]} {t(`project.safety.${project.safety_level}`)}
            </span>
          </div>

          <VideoPlayer
            url={project.video_url}
            poster={project.poster_url}
            icon={project.category_icon}
            onEnded={() => setVideoEnded(true)}
          />

          {project.safety_text && (
            <section className={`safety safety--${project.safety_level}`} role="note">
              <h2>⚠️ {t("project.safetyTitle")}</h2>
              <p>{tr(project.safety_text)}</p>
            </section>
          )}

          <section className="card">
            <h2>{t("project.materials")}</h2>
            <ul className="bullets">
              {(tr<string[]>(project.materials) ?? []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="card">
            <h2>{t("project.steps")}</h2>
            <ol className="steps">
              {(tr<string[]>(project.steps) ?? []).map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
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
            className="button button--block"
            disabled={isDone || !unlocked || saving}
            onClick={() => void markDone()}
          >
            {isDone
              ? t("project.alreadyDone")
              : unlocked
                ? t("project.done")
                : t("project.doneWait", { count: secondsLeft })}
          </button>
        </div>
      )}
    </main>
  );
}
