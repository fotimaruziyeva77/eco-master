import { Emoji } from "./Emoji";

/**
 * A badge drawn as a medal: a ribbon and a gold rim around the badge's picture, so it reads as
 * an award and not as one more waste-type icon. Locked badges are grey.
 */
export function Medal({ icon, locked, size = "md" }: { icon: string; locked?: boolean; size?: "md" | "lg" }) {
  const className = ["medal", size === "lg" && "medal--lg", locked && "is-locked"].filter(Boolean).join(" ");
  return (
    <span className={className} aria-hidden="true">
      <span className="medal__ribbon" />
      <span className="medal__disc">
        <Emoji char={icon} />
      </span>
    </span>
  );
}
