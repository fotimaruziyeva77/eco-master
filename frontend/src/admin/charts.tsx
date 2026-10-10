/** Small SVG charts: no chart library for a handful of lines and bars. */

type Series = { label: string; color: string; values: number[]; kind?: "line" | "bar" };

const W = 640;
const H = 200;
const PAD = { top: 12, right: 12, bottom: 24, left: 34 };

function niceMax(value: number): number {
  if (value <= 5) return 5;
  const power = 10 ** Math.floor(Math.log10(value));
  return Math.ceil(value / power) * power;
}

export function DayChart({ days, series, title }: { days: string[]; series: Series[]; title: string }) {
  const max = niceMax(Math.max(1, ...series.flatMap((s) => s.values)));
  const innerW = W - PAD.left - PAD.right;
  const innerH = H - PAD.top - PAD.bottom;
  const step = days.length > 1 ? innerW / (days.length - 1) : innerW;
  const x = (i: number) => PAD.left + (days.length > 1 ? i * step : innerW / 2);
  const y = (v: number) => PAD.top + innerH - (v / max) * innerH;
  const bars = series.filter((s) => s.kind === "bar");
  const barWidth = Math.max(2, Math.min(18, (innerW / Math.max(1, days.length)) * 0.7) / Math.max(1, bars.length));
  const labelEvery = Math.ceil(days.length / 8);

  return (
    <div className="a-chart">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={title}>
        {[0, 0.25, 0.5, 0.75, 1].map((f) => (
          <g key={f}>
            <line x1={PAD.left} x2={W - PAD.right} y1={y(max * f)} y2={y(max * f)} stroke="var(--line)" />
            <text x={PAD.left - 6} y={y(max * f) + 4} textAnchor="end" fontSize="11" fill="var(--hint)">
              {Math.round(max * f)}
            </text>
          </g>
        ))}
        {days.map((day, i) =>
          i % labelEvery === 0 || i === days.length - 1 ? (
            <text key={day} x={x(i)} y={H - 6} textAnchor="middle" fontSize="11" fill="var(--hint)">
              {day.slice(8, 10)}.{day.slice(5, 7)}
            </text>
          ) : null,
        )}
        {bars.map((s, b) =>
          s.values.map((v, i) => (
            <rect
              key={`${s.label}-${i}`}
              x={x(i) - (barWidth * bars.length) / 2 + b * barWidth}
              y={y(v)}
              width={barWidth}
              height={Math.max(0, PAD.top + innerH - y(v))}
              rx={2}
              fill={s.color}
            >
              <title>{`${days[i]}: ${s.label} ${v}`}</title>
            </rect>
          )),
        )}
        {series
          .filter((s) => s.kind !== "bar")
          .map((s) => (
            <g key={s.label}>
              <polyline
                fill="none"
                stroke={s.color}
                strokeWidth={2.5}
                strokeLinejoin="round"
                points={s.values.map((v, i) => `${x(i)},${y(v)}`).join(" ")}
              />
              {s.values.map((v, i) => (
                <circle key={i} cx={x(i)} cy={y(v)} r={days.length > 40 ? 0 : 3} fill={s.color}>
                  <title>{`${days[i]}: ${s.label} ${v}`}</title>
                </circle>
              ))}
            </g>
          ))}
      </svg>
      <div className="a-legend">
        {series.map((s) => (
          <span key={s.label}>
            <i style={{ background: s.color }} />
            {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}

export function Meter({ label, value, total }: { label: string; value: number; total: number }) {
  const share = total > 0 ? value / total : 0;
  return (
    <div className="a-meter">
      <span>{label}</span>
      <span className="a-meter-bar">
        <span style={{ width: `${Math.round(share * 100)}%` }} />
      </span>
      <span className="a-small" style={{ textAlign: "right" }}>
        {value} · {Math.round(share * 100)}%
      </span>
    </div>
  );
}
