import { Check, ChevronLeft, ChevronRight, Play, Volume2, VolumeX } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useParams } from "react-router";

import { api, type ProjectDetail } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { SubpageHeader } from "../components/ui";
import { useBack } from "../hooks/useBack";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";
import { stepTimes, stepsWatched } from "../steps";
import { haptic } from "../telegram";

/**
 * A project step by step: each step's part of the video plays over and over under its text,
 * so the child can do it along. The last step brings them back to "I did it".
 */
export function ProjectStepsScreen() {
  const { slug = "" } = useParams();
  const { t } = useTranslation();
  const tr = useTr();
  const location = useLocation();
  const passed = location.state as { project?: ProjectDetail; step?: number } | null;
  // From the project screen the project comes along; opened directly it is loaded.
  const data = useLoad(
    () => (passed?.project?.slug === slug ? Promise.resolve(passed.project) : api.project(slug)),
    [slug],
  );
  const project = data.data;
  const back = useBack(`/projects/${slug}`);
  const steps = tr<string[]>(project?.steps) ?? [];
  const times = stepTimes(project, steps.length);
  const pictures = project?.step_pictures ?? [];

  const [index, setIndex] = useState(passed?.step ?? 0);
  const [muted, setMuted] = useState(true);
  const [paused, setPaused] = useState(false);
  const player = useRef<HTMLVideoElement>(null);
  const from = times?.[index] ?? 0;
  const to = times && index + 1 < times.length ? times[index + 1] : null;

  // To the start of the step whenever the step changes (once the video knows its length).
  const start = useCallback(() => {
    const video = player.current;
    if (!video || video.readyState < 1) return;
    video.currentTime = from;
    setPaused(false);
    video.play().catch(() => setPaused(true));
  }, [from]);
  useEffect(start, [start]);

  function go(next: number) {
    haptic.tap();
    setIndex(next);
  }

  function toggle() {
    const video = player.current;
    if (!video) return;
    if (video.paused) {
      void video.play().catch(() => undefined);
      setPaused(false);
    } else {
      video.pause();
      setPaused(true);
    }
  }

  function finish() {
    haptic.success();
    stepsWatched.add(slug);
    back();
  }

  return (
    <main className="screen steps-screen">
      <SubpageHeader
        onBack={back}
        title={times ? t("steps.counter", { step: index + 1, count: steps.length }) : undefined}
        right={
          times && (
            <button
              type="button"
              className="icon-button"
              onClick={() => setMuted((m) => !m)}
              aria-label={muted ? t("video.soundOn") : t("video.soundOff")}
            >
              {muted ? <VolumeX size={20} /> : <Volume2 size={20} />}
            </button>
          )
        }
      />
      {data.loading && !project && <InlineLoading />}
      {data.error !== undefined && !project && <InlineError error={data.error} onRetry={data.reload} />}
      {project && !times && <p className="empty">{t("steps.none")}</p>}

      {project && times && (
        <div className="stack stack--lg">
          <div className="steps-screen__video">
            <video
              ref={player}
              src={project.video_url ?? undefined}
              poster={pictures[index] ?? project.poster_url ?? undefined}
              muted={muted}
              playsInline
              preload="auto"
              onClick={toggle}
              onLoadedMetadata={start}
              onTimeUpdate={(e) => {
                // The step's part plays over and over.
                if (to !== null && e.currentTarget.currentTime >= to) e.currentTarget.currentTime = from;
              }}
              onEnded={(e) => {
                e.currentTarget.currentTime = from;
                void e.currentTarget.play().catch(() => undefined);
              }}
            />
            {paused && (
              <span className="feed__paused" aria-hidden="true">
                <Play size={48} fill="currentColor" />
              </span>
            )}
          </div>

          <ol className="steps-dots" aria-hidden="true">
            {steps.map((step, i) => (
              <li key={step} className={i === index ? "is-on" : i < index ? "is-done" : undefined} />
            ))}
          </ol>

          <div className="steps-screen__text" aria-live="polite">
            <span className="step-card__num">{index + 1}</span>
            <p>{steps[index]}</p>
          </div>

          <div className="steps-screen__nav">
            <button
              type="button"
              className="btn btn--soft"
              disabled={index === 0}
              onClick={() => go(index - 1)}
              aria-label={t("steps.prev")}
            >
              <ChevronLeft size={20} />
            </button>
            {index + 1 < steps.length ? (
              <button type="button" className="btn" onClick={() => go(index + 1)}>
                {t("steps.next")} <ChevronRight size={20} />
              </button>
            ) : (
              <button type="button" className="btn" onClick={finish}>
                <Check size={20} /> {t("steps.finish")}
              </button>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
