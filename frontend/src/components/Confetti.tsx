import type { CSSProperties } from "react";

const CONFETTI_COLORS = ["#10b981", "#f59e0b", "#0ea5e9", "#ec4899", "#84cc16", "#8b5cf6"];

/** Paper pieces falling over a celebration (CSS only). */
export function Confetti() {
  return (
    <div className="confetti" aria-hidden="true">
      {Array.from({ length: 28 }, (_, i) => (
        <span
          key={i}
          style={
            {
              "--x": `${(i * 37) % 100}%`,
              "--delay": `${(i % 7) * 0.12}s`,
              "--color": CONFETTI_COLORS[i % CONFETTI_COLORS.length],
              "--turn": `${(i % 2 ? 1 : -1) * (180 + ((i * 53) % 360))}deg`,
            } as CSSProperties
          }
        />
      ))}
    </div>
  );
}
