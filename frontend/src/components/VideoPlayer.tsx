import { Play } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { openExternal } from "../telegram";

type Source = { kind: "youtube"; id: string } | { kind: "file"; url: string } | { kind: "link"; url: string };

export function parseVideo(url: string): Source {
  const youtube = url.match(
    /(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/)|youtu\.be\/)([A-Za-z0-9_-]{6,})/,
  );
  if (youtube) return { kind: "youtube", id: youtube[1] };
  if (/\.(mp4|webm|m3u8)(\?|$)/i.test(url)) return { kind: "file", url };
  return { kind: "link", url };
}

type Props = {
  url: string | null;
  poster: string | null;
  icon: string;
  onEnded: () => void;
  onPlay?: () => void;
};

/** Loads nothing until tapped — saves traffic on slow connections (TZ 8.3). */
export function VideoPlayer({ url, poster, icon, onEnded, onPlay }: Props) {
  const { t } = useTranslation();
  const [playing, setPlaying] = useState(false);

  if (!url) {
    return (
      <div className="video video--empty">
        <span className="video__icon" aria-hidden="true">
          {icon}
        </span>
        <span className="strong">🎬 {t("project.videoSoon")}</span>
      </div>
    );
  }

  const source = parseVideo(url);
  if (!playing) {
    return (
      <button
        type="button"
        className="video video--poster"
        style={poster ? { backgroundImage: `url(${poster})` } : undefined}
        onClick={() => {
          onPlay?.();
          if (source.kind === "link") openExternal(source.url);
          else setPlaying(true);
        }}
        aria-label={t("project.play")}
      >
        {!poster && (
          <span className="video__icon" aria-hidden="true">
            {icon}
          </span>
        )}
        <span className="video__play" aria-hidden="true">
          <Play size={30} fill="currentColor" />
        </span>
      </button>
    );
  }

  if (source.kind === "youtube") {
    return (
      <div className="video">
        <iframe
          src={`https://www.youtube-nocookie.com/embed/${source.id}?autoplay=1&playsinline=1&rel=0`}
          title={t("project.play")}
          allow="autoplay; encrypted-media; picture-in-picture"
          allowFullScreen
        />
      </div>
    );
  }
  return (
    <div className="video">
      <video
        src={source.kind === "file" ? source.url : undefined}
        poster={poster ?? undefined}
        controls
        autoPlay
        playsInline
        onEnded={onEnded}
      />
    </div>
  );
}
