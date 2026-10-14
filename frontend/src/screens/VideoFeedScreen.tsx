import { ArrowLeft, Hammer, Play, Volume2, VolumeX } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";

import { trackVideo } from "../analytics";
import { api, type VideoCard } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { Emoji } from "../components/Emoji";
import { PROJECT_POINTS } from "../components/ProjectCard";
import { useBack } from "../hooks/useBack";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";
import { useNoVerticalSwipes, useTelegramBackButton } from "../telegram";

/**
 * The home screen's videos full screen, one under another: swipe up for the next. Only the video
 * in view plays (muted until the sound button is pressed); the ones next to it load ahead.
 */
export function VideoFeedScreen() {
  const { slug = "" } = useParams();
  const { t } = useTranslation();
  const back = useBack("/");
  const feed = useLoad(() => api.videos(), []);
  const [muted, setMuted] = useState(true);
  const [active, setActive] = useState(0);
  const list = useRef<HTMLDivElement>(null);
  useTelegramBackButton(back);
  // A swipe up or down moves between videos here; it must not close the Mini App.
  useNoVerticalSwipes();

  // Open at the video that was tapped.
  useEffect(() => {
    const videos = feed.data;
    if (!videos || !list.current) return;
    const start = Math.max(0, videos.findIndex((v) => v.slug === slug));
    setActive(start);
    list.current.children[start]?.scrollIntoView({ block: "start" });
  }, [feed.data, slug]);

  return (
    <main className="feed">
      <button type="button" className="feed__button feed__button--back" onClick={back} aria-label={t("common.back")}>
        <ArrowLeft size={22} />
      </button>
      <button
        type="button"
        className="feed__button feed__button--sound"
        onClick={() => setMuted((m) => !m)}
        aria-label={muted ? t("video.soundOn") : t("video.soundOff")}
      >
        {muted ? <VolumeX size={22} /> : <Volume2 size={22} />}
      </button>
      {feed.loading && !feed.data && <InlineLoading />}
      {feed.error !== undefined && !feed.data && <InlineError error={feed.error} onRetry={feed.reload} />}
      {feed.data?.length === 0 && <p className="feed__empty">{t("video.empty")}</p>}
      <div className="feed__list" ref={list}>
        {feed.data?.map((video, i) => (
          <FeedItem
            key={video.slug}
            video={video}
            index={i}
            active={i === active}
            near={Math.abs(i - active) <= 1}
            muted={muted}
            onSeen={setActive}
          />
        ))}
      </div>
    </main>
  );
}

type ItemProps = {
  video: VideoCard;
  index: number;
  active: boolean;
  /** In view or next to it: the file loads; further away only the cover picture. */
  near: boolean;
  muted: boolean;
  onSeen: (index: number) => void;
};

function FeedItem({ video, index, active, near, muted, onSeen }: ItemProps) {
  const { t } = useTranslation();
  const tr = useTr();
  const box = useRef<HTMLElement>(null);
  const player = useRef<HTMLVideoElement>(null);
  const [paused, setPaused] = useState(false);
  const [wide, setWide] = useState(false);
  const [progress, setProgress] = useState(0);
  const played = useRef(false);
  const finished = useRef(false);

  // Mostly on screen: this one is the video being watched.
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const observer = new IntersectionObserver(([entry]) => entry.intersectionRatio >= 0.6 && onSeen(index), {
      threshold: [0.6],
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [onSeen, index]);

  useEffect(() => {
    const v = player.current;
    if (!v) return;
    if (!active) {
      v.pause();
      return;
    }
    setPaused(false);
    v.play().catch(() => setPaused(true));
    if (!played.current) {
      played.current = true;
      trackVideo("video_play", video.slug);
    }
  }, [active, near, video.slug]);

  function toggle() {
    const v = player.current;
    if (!v) return;
    if (v.paused) {
      void v.play().catch(() => undefined);
      setPaused(false);
    } else {
      v.pause();
      setPaused(true);
    }
  }

  return (
    <section className="feed__item" ref={box} aria-label={tr(video.title)}>
      {near ? (
        <video
          ref={player}
          className={wide ? "feed__video is-wide" : "feed__video"}
          src={video.video_url}
          poster={video.poster_url ?? undefined}
          muted={muted}
          loop
          playsInline
          preload={active ? "auto" : "metadata"}
          onClick={toggle}
          onLoadedMetadata={(e) => setWide(e.currentTarget.videoWidth > e.currentTarget.videoHeight)}
          onTimeUpdate={(e) => {
            const v = e.currentTarget;
            if (!v.duration) return;
            setProgress((v.currentTime / v.duration) * 100);
            // It loops, so "watched" is the first time it gets near the end.
            if (!finished.current && v.currentTime >= v.duration * 0.95) {
              finished.current = true;
              trackVideo("video_complete", video.slug);
            }
          }}
        />
      ) : (
        video.poster_url && <img className="feed__video" src={video.poster_url} alt="" loading="lazy" />
      )}
      {paused && (
        <span className="feed__paused" aria-hidden="true">
          <Play size={56} fill="currentColor" />
        </span>
      )}
      <div className="feed__info">
        <h2>{tr(video.title)}</h2>
        <div className="chips">
          <span className="chip chip--sm feed__chip">
            <Emoji char={video.category_icon} /> {t("common.minutes", { count: video.duration_min })}
          </span>
          <span className="chip chip--amber chip--sm">
            <Emoji char="⭐" /> +{PROJECT_POINTS}
          </span>
        </div>
        <Link className="btn btn--block" to={`/projects/${video.slug}`}>
          <Hammer size={18} aria-hidden="true" /> {t("video.howTo")}
        </Link>
      </div>
      <div className="feed__progress" aria-hidden="true">
        <span style={{ width: `${progress}%` }} />
      </div>
    </section>
  );
}
