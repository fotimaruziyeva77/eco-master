import { STAGE_VIEW, treeGrowth, treeParts, type TreePart } from "./treeDrawing";

type Props = {
  points: number;
  size?: number;
  /** Show the tree up close (icons) instead of its real size on the hill. */
  fit?: boolean;
  /** Announced as a picture with this name; without it the tree is decoration. */
  label?: string;
};

/** "My tree" for these points. A new stage pops in. */
export function Tree({ points, size = 96, fit = false, label }: Props) {
  const growth = treeGrowth(points);
  const parts = treeParts(growth);
  const [x, y, side] = fit ? STAGE_VIEW[growth.stage] : [0, 0, 200];
  return (
    <svg
      className="tree"
      viewBox={`${x} ${y} ${side} ${side}`}
      width={size}
      height={size}
      role={label ? "img" : undefined}
      aria-label={label}
      aria-hidden={label ? undefined : true}
    >
      {!fit && (
        // A sun and a cloud, so the sky is not empty while the tree is still small.
        <g>
          <circle cx={170} cy={30} r={15} fill="#fde68a" />
          <ellipse cx={34} cy={42} rx={14} ry={9} fill="#ffffff" opacity={0.9} />
          <ellipse cx={48} cy={38} rx={13} ry={11} fill="#ffffff" opacity={0.9} />
          <ellipse cx={60} cy={43} rx={11} ry={8} fill="#ffffff" opacity={0.9} />
        </g>
      )}
      <g key={growth.stage} className="tree__grow">
        {parts.map((part, i) => (
          <Part key={i} part={part} />
        ))}
      </g>
    </svg>
  );
}

function Part({ part }: { part: TreePart }) {
  switch (part.kind) {
    case "circle":
      return <circle cx={part.cx} cy={part.cy} r={part.r} fill={part.fill} />;
    case "ellipse":
      return (
        <ellipse
          cx={part.cx}
          cy={part.cy}
          rx={part.rx}
          ry={part.ry}
          fill={part.fill}
          transform={part.rotate ? `rotate(${part.rotate} ${part.cx} ${part.cy})` : undefined}
        />
      );
    case "poly":
      return <polygon points={part.points.map((point) => point.join(",")).join(" ")} fill={part.fill} />;
    case "line":
      return (
        <line
          x1={part.x1}
          y1={part.y1}
          x2={part.x2}
          y2={part.y2}
          stroke={part.color}
          strokeWidth={part.width}
          strokeLinecap="round"
        />
      );
  }
}
