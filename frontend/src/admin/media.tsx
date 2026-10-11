import { Film, ImagePlus, LoaderCircle, RefreshCw, Trash2, Upload, X } from "lucide-react";
import { useEffect, useRef, useState, type DragEvent } from "react";

import { adminApi, errorText, messageFor, type MediaStatus } from "./api";

export type MediaKind = "video" | "image" | "item_image";

const VIDEO_MAX = 500 * 1024 * 1024;
const PICTURE_MAX = 15 * 1024 * 1024;
const PICTURE_TYPES = ["image/jpeg", "image/png", "image/webp"];
const VIDEO_EXTENSIONS = /\.(mp4|mov|m4v|webm|mkv|3gp|avi)$/i;

type State =
  | { phase: "idle" }
  | { phase: "uploading"; name: string; percent: number; abort: AbortController }
  | { phase: "processing"; name: string; videoId: number }
  | { phase: "error"; message: string };

// Asked once per page: a server that refuses a video only after the upload started would
// break the upload in the browser instead of saying why.
let status: Promise<MediaStatus> | null = null;
const mediaStatus = () => (status ??= adminApi.mediaStatus().catch((error: unknown) => {
  status = null;
  throw error;
}));

/** Files that are uploaded, converted or waiting: leaving the page would lose them. */
let busyFields = 0;
const warnOnLeave = (e: BeforeUnloadEvent) => e.preventDefault();

function useLeaveWarning(busy: boolean) {
  useEffect(() => {
    if (!busy) return;
    busyFields += 1;
    if (busyFields === 1) window.addEventListener("beforeunload", warnOnLeave);
    return () => {
      busyFields -= 1;
      if (busyFields === 0) window.removeEventListener("beforeunload", warnOnLeave);
    };
  }, [busy]);
}

function checkFile(kind: MediaKind, file: File): string | null {
  if (kind === "video") {
    if (!file.type.startsWith("video/") && !VIDEO_EXTENSIONS.test(file.name)) return "Bu video fayl emas.";
    if (file.size > VIDEO_MAX) return "Video juda katta: 500 MB gacha bo'lsin.";
    return null;
  }
  if (!PICTURE_TYPES.includes(file.type)) return "Faqat JPG, PNG yoki WebP rasm yuklash mumkin.";
  if (file.size > PICTURE_MAX) return "Rasm juda katta: 15 MB gacha bo'lsin.";
  return null;
}

/**
 * A picture or video uploaded from the computer, instead of a link to another site.
 * Pictures are ready at once; a video is converted on the server, which takes a minute or two.
 */
export function MediaField({
  id,
  kind,
  value,
  invalid,
  onChange,
  onExtra,
}: {
  id: string;
  kind: MediaKind;
  value: string | null;
  invalid?: boolean;
  onChange: (value: string | null) => void;
  /** Other fields a finished upload can fill: the cover picture of a video. */
  onExtra?: (patch: Record<string, string>) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<State>({ phase: "idle" });
  const [dragging, setDragging] = useState(false);
  const busy = state.phase === "uploading" || state.phase === "processing";
  useLeaveWarning(busy);

  // A video is converted on the server: ask for its state until it is ready.
  const videoId = state.phase === "processing" ? state.videoId : null;
  useEffect(() => {
    if (videoId === null) return;
    let alive = true;
    let timer = 0;
    const poll = async () => {
      try {
        const video = await adminApi.videoState(videoId);
        if (!alive) return;
        if (video.status === "ready" && video.url) {
          onChange(video.url);
          if (video.poster_url) onExtra?.({ poster_url: video.poster_url });
          setState({ phase: "idle" });
        } else if (video.status === "failed") {
          setState({ phase: "error", message: messageFor(video.error ?? "video_unreadable") });
        } else {
          timer = window.setTimeout(() => void poll(), 2000);
        }
      } catch (error) {
        if (alive) setState({ phase: "error", message: errorText(error) });
      }
    };
    timer = window.setTimeout(() => void poll(), 1500);
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
    // onChange/onExtra change on every render of the form; the poll only needs the id.
  }, [videoId]);

  async function send(file: File) {
    const problem = checkFile(kind, file);
    if (problem) {
      setState({ phase: "error", message: problem });
      return;
    }
    const abort = new AbortController();
    const progress = (percent: number) =>
      setState((s) => (s.phase === "uploading" ? { ...s, percent } : s));
    setState({ phase: "uploading", name: file.name, percent: 0, abort });
    try {
      if (kind === "video") {
        if (!(await mediaStatus()).video) {
          setState({ phase: "error", message: messageFor("no_ffmpeg") });
          return;
        }
        const video = await adminApi.uploadVideo(file, progress, abort.signal);
        setState({ phase: "processing", name: file.name, videoId: video.id });
      } else {
        const picture = await adminApi.uploadPicture(file, kind === "item_image" ? "item" : "picture", progress, abort.signal);
        onChange(picture.url);
        setState({ phase: "idle" });
      }
    } catch (error) {
      if (abort.signal.aborted) setState({ phase: "idle" });
      else setState({ phase: "error", message: errorText(error) });
    }
  }

  function pick(files: FileList | null) {
    const file = files?.[0];
    if (file) void send(file);
    if (input.current) input.current.value = "";
  }

  function drop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    if (!busy) pick(e.dataTransfer.files);
  }

  const accept = kind === "video" ? "video/*" : PICTURE_TYPES.join(",");
  const external = value !== null && /^https?:\/\//.test(value);

  return (
    <div
      className={["a-media", dragging && "is-dragging", invalid && "is-invalid"].filter(Boolean).join(" ")}
      onDragOver={(e) => {
        e.preventDefault();
        if (!busy) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={drop}
    >
      <input
        ref={input}
        id={id}
        type="file"
        accept={accept}
        hidden
        onChange={(e) => pick(e.target.files)}
      />

      {state.phase === "uploading" && (
        <div className="a-media__status" role="status">
          <Upload size={18} aria-hidden="true" />
          <div className="a-media__progress">
            <strong>Yuklanmoqda… {state.percent}%</strong>
            <span className="a-muted a-small">{state.name}</span>
            <div className="a-media__bar">
              <span style={{ width: `${state.percent}%` }} />
            </div>
          </div>
          <button type="button" className="a-icon-btn" onClick={() => state.abort.abort()} aria-label="To'xtatish">
            <X size={15} />
          </button>
        </div>
      )}

      {state.phase === "processing" && (
        <div className="a-media__status" role="status">
          <LoaderCircle size={18} className="a-spin" aria-hidden="true" />
          <div className="a-media__progress">
            <strong>Video tayyorlanmoqda…</strong>
            <span className="a-muted a-small">
              {state.name}: server siqib, muqova oladi. 1–3 daqiqa; sahifani yopmang.
            </span>
          </div>
        </div>
      )}

      {!busy && value && (
        <div className="a-media__preview">
          {external ? (
            <a className="a-media__link" href={value} target="_blank" rel="noreferrer">
              <Film size={16} aria-hidden="true" /> Tashqi havola: {value}
            </a>
          ) : kind === "video" ? (
            <video className="a-media__video" src={value} controls preload="metadata" playsInline />
          ) : (
            <img className={kind === "item_image" ? "a-media__img a-media__img--item" : "a-media__img"} src={value} alt="" />
          )}
          <div className="a-row">
            <button type="button" className="a-btn a-btn--soft a-btn--sm" onClick={() => input.current?.click()}>
              <RefreshCw size={14} aria-hidden="true" /> Almashtirish
            </button>
            <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => onChange(null)}>
              <Trash2 size={14} aria-hidden="true" /> Olib tashlash
            </button>
          </div>
        </div>
      )}

      {!busy && !value && (
        <button type="button" className="a-media__drop" onClick={() => input.current?.click()}>
          {kind === "video" ? <Film size={26} aria-hidden="true" /> : <ImagePlus size={26} aria-hidden="true" />}
          <strong>{kind === "video" ? "Video yuklash" : "Rasm yuklash"}</strong>
          <span className="a-muted a-small">Faylni shu yerga tashlang yoki bosib tanlang</span>
        </button>
      )}

      {state.phase === "error" && (
        <p className="a-error" role="alert">
          {state.message}
        </p>
      )}
    </div>
  );
}
