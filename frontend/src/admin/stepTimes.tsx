import { Play, Timer, X } from "lucide-react";
import { useRef } from "react";

/** "0:12.5" → 12.5; also plain seconds. Null for an empty or unreadable entry. */
export function parseTime(text: string): number | null {
  const value = text.trim();
  if (!value) return null;
  const match = value.match(/^(?:(\d+):)?(\d+(?:[.,]\d)?)$/);
  if (!match) return null;
  const seconds = Number(match[2].replace(",", "."));
  return Math.round(((match[1] ? Number(match[1]) * 60 : 0) + seconds) * 10) / 10;
}

/** 12.5 → "0:12.5". */
export function formatTime(seconds: number): string {
  const whole = Math.floor(seconds);
  const tenth = Math.round((seconds - whole) * 10);
  const s = String(whole % 60).padStart(2, "0");
  return `${Math.floor(whole / 60)}:${s}${tenth ? `.${tenth}` : ""}`;
}

type Props = {
  value: (number | null)[] | null;
  videoUrl: string | null;
  steps: string[];
  invalid: boolean;
  onChange: (value: (number | null)[] | null) => void;
};

/**
 * Where each step starts in the uploaded video. Play the video and press ⏱ at a step: its time is
 * taken from the player. ▶ jumps there to check. The Mini App then shows the steps one by one.
 */
export function StepTimesEditor({ value, videoUrl, steps, invalid, onChange }: Props) {
  const player = useRef<HTMLVideoElement>(null);
  if (!videoUrl || !/^\/media\/v\/[0-9a-f]{24}\.mp4$/.test(videoUrl)) {
    return <p className="a-help">Avval videoni yuklang: vaqtlar shu yerga yuklangan videoda belgilanadi.</p>;
  }
  if (steps.length === 0) {
    return <p className="a-help">Avval qadamlarni (o'zbekcha) yozing.</p>;
  }
  const times = steps.map((_, i) => value?.[i] ?? null);

  function set(i: number, seconds: number | null) {
    const next = times.map((t, k) => (k === i ? seconds : t));
    onChange(next.every((t) => t === null) ? null : next);
  }

  function mark(i: number) {
    const video = player.current;
    if (video) set(i, Math.round(video.currentTime * 10) / 10);
  }

  function show(i: number) {
    const video = player.current;
    const seconds = times[i];
    if (!video || seconds === null) return;
    video.currentTime = seconds;
    void video.play().catch(() => undefined);
  }

  return (
    <div className={`a-steps${invalid ? " is-invalid" : ""}`}>
      <video ref={player} className="a-steps__video" src={videoUrl} controls playsInline preload="metadata" />
      <ol className="a-steps__list">
        {steps.map((step, i) => (
          <li key={i} className="a-steps__row">
            <span className="a-steps__text">
              <strong>{i + 1}.</strong> {step}
            </span>
            <input
              className="a-input a-steps__time"
              aria-label={`${i + 1}-qadam vaqti`}
              placeholder="0:00"
              // Keyed by value: typing is kept as text until it can be read as a time.
              key={times[i] ?? "empty"}
              defaultValue={times[i] === null ? "" : formatTime(times[i]!)}
              onBlur={(e) => set(i, parseTime(e.target.value))}
            />
            <button type="button" className="a-btn a-btn--sm" onClick={() => mark(i)} title="Videodagi joriy vaqtni olish">
              <Timer size={14} /> Shu yerdan
            </button>
            <button
              type="button"
              className="a-icon-btn"
              onClick={() => show(i)}
              disabled={times[i] === null}
              aria-label={`${i + 1}-qadamni ko'rish`}
            >
              <Play size={14} />
            </button>
          </li>
        ))}
      </ol>
      {value && (
        <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => onChange(null)}>
          <X size={14} /> Vaqtlarni tozalash
        </button>
      )}
    </div>
  );
}
