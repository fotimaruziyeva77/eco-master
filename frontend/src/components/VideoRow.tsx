import { Check, Play } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { VideoCard } from "../api/client";
import { useTr } from "../i18n/tr";
import { Emoji } from "./Emoji";

/** Craft videos in a row on the home screen; a tap opens them full screen, one after another. */
export function VideoRow({ videos }: { videos: VideoCard[] }) {
  const { t } = useTranslation();
  const tr = useTr();
  return (
    <section className="stack" aria-label={t("home.videos")}>
      <h2>{t("home.videos")}</h2>
      <ul className="video-row">
        {videos.map((video) => (
          <li key={video.slug}>
            <Link className="video-tile" to={`/videos/${video.slug}`}>
              {video.poster_url ? (
                <img className="video-tile__poster" src={video.poster_url} alt="" loading="lazy" />
              ) : (
                <span className="video-tile__icon" aria-hidden="true">
                  <Emoji char={video.category_icon} />
                </span>
              )}
              <span className="video-tile__play" aria-hidden="true">
                <Play size={16} fill="currentColor" />
              </span>
              {video.done && (
                <span className="video-tile__done" aria-label={t("project.alreadyDone")}>
                  <Check size={14} />
                </span>
              )}
              <span className="video-tile__title">{tr(video.title)}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
