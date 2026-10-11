import { useState } from "react";

/**
 * Emoji drawn the same on every phone (Microsoft Fluent Emoji, scripts/emoji.mjs) instead of
 * the phone's own font, which differs between iPhone, Samsung, Xiaomi and computers. Sized like
 * text (1em), so it fits wherever an emoji character did. Anything the set lacks falls back to
 * the phone's emoji.
 */
export function emojiSrc(char: string): string | null {
  const points = [...char]
    .map((c) => c.codePointAt(0)!.toString(16).padStart(4, "0"))
    .filter((p) => p !== "fe0f");
  return points.length ? `/emoji/${points.join("-")}.svg` : null;
}

export function Emoji({
  char,
  label,
  className,
}: {
  char: string | null | undefined;
  /** Spoken name, when the picture means something on its own; otherwise it is decorative. */
  label?: string;
  className?: string;
}) {
  const [failed, setFailed] = useState<string | null>(null);
  if (!char) return null;
  const src = emojiSrc(char);
  const classes = className ? `emoji ${className}` : "emoji";
  if (!src || failed === char) {
    return (
      <span className={`${classes} emoji--text`} role={label ? "img" : undefined} aria-label={label} aria-hidden={label ? undefined : true}>
        {char}
      </span>
    );
  }
  return (
    <img
      className={classes}
      src={src}
      alt={label ?? ""}
      aria-hidden={label ? undefined : true}
      draggable={false}
      decoding="async"
      onError={() => setFailed(char)}
    />
  );
}
