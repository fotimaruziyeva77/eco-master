// "My tree": a picture that grows with the points — a seed, a sprout, a sapling, a young tree
// in bloom, a big tree with apples. The same drawing is made on the server for the Stories
// picture (backend/app/tree.py); keep the two in step.

export const TREE_THRESHOLDS = [0, 100, 500, 1000, 2500];
/** Past the top level an apple grows for every this many points (up to eight). */
const POINTS_PER_FRUIT = 300;

export type TreePart =
  | { kind: "circle"; cx: number; cy: number; r: number; fill: string }
  | { kind: "ellipse"; cx: number; cy: number; rx: number; ry: number; fill: string; rotate?: number }
  | { kind: "poly"; points: [number, number][]; fill: string }
  | { kind: "line"; x1: number; y1: number; x2: number; y2: number; width: number; color: string };

const C = {
  leafDark: "#15803d",
  leaf: "#22c55e",
  leafLight: "#4ade80",
  stem: "#16a34a",
  trunk: "#92582a",
  grass: "#86d36b",
  grassDark: "#65b84a",
  seed: "#a0632b",
  seedShine: "#c58a4f",
  flower: "#f472b6",
  flowerMiddle: "#fde047",
  fruit: "#ef4444",
  fruitShine: "#fca5a5",
};

export type TreeGrowth = { stage: number; progress: number; fruits: number };

/** Part of the 200×200 drawing to show up close for each stage (x, y, side): small icons and
 * the Stories picture look full even while the tree is only a seed. */
export const STAGE_VIEW: [number, number, number][] = [
  [56, 112, 88],
  [45, 80, 110],
  [35, 60, 130],
  [10, 15, 180],
  [0, 0, 200],
];

/** Stage 0–4 follows the level; progress 0–1 is the way to the next one. */
export function treeGrowth(points: number): TreeGrowth {
  let stage = 0;
  TREE_THRESHOLDS.forEach((min, i) => {
    if (points >= min) stage = i;
  });
  const min = TREE_THRESHOLDS[stage];
  const next = TREE_THRESHOLDS[stage + 1];
  const progress = next === undefined ? 1 : Math.min(1, Math.max(0, (points - min) / (next - min)));
  const fruits = next === undefined ? Math.min(8, 1 + Math.floor((points - min) / POINTS_PER_FRUIT)) : 0;
  return { stage, progress, fruits };
}

const circle = (cx: number, cy: number, r: number, fill: string): TreePart => ({ kind: "circle", cx, cy, r, fill });

/** The drawing in a 200×200 box, ground at y = 172. */
export function treeParts({ stage, progress: p, fruits }: TreeGrowth): TreePart[] {
  const parts: TreePart[] = [
    { kind: "ellipse", cx: 100, cy: 176, rx: 82, ry: 14, fill: C.grassDark },
    { kind: "ellipse", cx: 100, cy: 173, rx: 78, ry: 11, fill: C.grass },
  ];

  if (stage === 0) {
    parts.push(
      { kind: "ellipse", cx: 100, cy: 171, rx: 12, ry: 8, fill: C.seed },
      { kind: "ellipse", cx: 96, cy: 168, rx: 4, ry: 2.2, fill: C.seedShine, rotate: -20 },
    );
    if (p >= 0.05) {
      const s = 0.4 + 0.6 * p;
      const top = 166 - 26 * s;
      parts.push(
        { kind: "line", x1: 100, y1: 166, x2: 100, y2: top, width: 4, color: C.stem },
        { kind: "ellipse", cx: 100 - 9 * s, cy: top - 2 * s, rx: 10 * s, ry: 5 * s, fill: C.leaf, rotate: -30 },
        { kind: "ellipse", cx: 100 + 9 * s, cy: top - 2 * s, rx: 10 * s, ry: 5 * s, fill: C.leafLight, rotate: 30 },
      );
    }
    return parts;
  }

  if (stage === 1) {
    const height = 44 + 30 * p;
    const top = 172 - height;
    parts.push({ kind: "line", x1: 100, y1: 172, x2: 100, y2: top, width: 5, color: C.stem });
    const sides: [number, number][] = [
      [0.55, -1],
      [0.4, 1],
      [0.25, -1],
    ];
    sides.slice(0, Math.floor(p * 4)).forEach(([at, side]) => {
      parts.push({
        kind: "ellipse",
        cx: 100 + side * 10,
        cy: 172 - height * at,
        rx: 11,
        ry: 5.5,
        fill: side < 0 ? C.leaf : C.leafLight,
        rotate: side * 25,
      });
    });
    parts.push(
      { kind: "ellipse", cx: 89, cy: top - 3, rx: 12, ry: 6, fill: C.leaf, rotate: -30 },
      { kind: "ellipse", cx: 111, cy: top - 3, rx: 12, ry: 6, fill: C.leafLight, rotate: 30 },
    );
    return parts;
  }

  if (stage === 2) {
    const s = 0.8 + 0.2 * p;
    const top = 172 - 62 * s;
    const cy = top - 14 * s;
    parts.push(
      { kind: "poly", points: [[95, 172], [105, 172], [103, top], [97, top]], fill: C.trunk },
      circle(100 - 16 * s, cy + 6 * s, 20 * s, C.leafDark),
      circle(100 + 16 * s, cy + 6 * s, 20 * s, C.leafDark),
      circle(100, cy - 4 * s, 24 * s, C.leaf),
      circle(100 - 14 * s, cy + 2 * s, 16 * s, C.leaf),
      circle(100 + 14 * s, cy + 2 * s, 16 * s, C.leaf),
      circle(100 - 8 * s, cy - 12 * s, 8 * s, C.leafLight),
    );
    return parts;
  }

  if (stage === 3) {
    const s = 0.85 + 0.15 * p;
    const top = 172 - 70 * s;
    const cy = top - 22 * s;
    parts.push(
      { kind: "poly", points: [[91, 172], [109, 172], [105, top], [95, top]], fill: C.trunk },
      circle(100 - 34 * s, cy + 10 * s, 24 * s, C.leafDark),
      circle(100 + 34 * s, cy + 10 * s, 24 * s, C.leafDark),
      circle(100, cy + 16 * s, 28 * s, C.leafDark),
      circle(100 - 22 * s, cy - 6 * s, 26 * s, C.leaf),
      circle(100 + 22 * s, cy - 6 * s, 26 * s, C.leaf),
      circle(100, cy - 18 * s, 30 * s, C.leaf),
      circle(100, cy + 6 * s, 26 * s, C.leaf),
      circle(100 - 14 * s, cy - 26 * s, 10 * s, C.leafLight),
      circle(100 + 26 * s, cy - 14 * s, 7 * s, C.leafLight),
    );
    const flowers: [number, number][] = [
      [-30, -4],
      [20, -26],
      [34, 8],
      [-8, 12],
      [-22, -30],
      [10, -2],
    ];
    flowers.slice(0, Math.floor(p * 7)).forEach(([dx, dy]) => {
      parts.push(circle(100 + dx * s, cy + dy * s, 4.5 * s, C.flower), circle(100 + dx * s, cy + dy * s, 1.8 * s, C.flowerMiddle));
    });
    return parts;
  }

  parts.push(
    { kind: "poly", points: [[80, 172], [120, 172], [110, 160], [106, 94], [94, 94], [90, 160]], fill: C.trunk },
    circle(58, 84, 28, C.leafDark),
    circle(142, 84, 28, C.leafDark),
    circle(100, 92, 32, C.leafDark),
    circle(70, 52, 26, C.leafDark),
    circle(130, 52, 26, C.leafDark),
    circle(76, 66, 30, C.leaf),
    circle(124, 66, 30, C.leaf),
    circle(100, 44, 32, C.leaf),
    circle(100, 76, 30, C.leaf),
    circle(56, 76, 20, C.leaf),
    circle(144, 76, 20, C.leaf),
    circle(86, 34, 11, C.leafLight),
    circle(128, 46, 8, C.leafLight),
    circle(64, 58, 7, C.leafLight),
  );
  const apples: [number, number][] = [
    [78, 60],
    [118, 40],
    [134, 74],
    [96, 84],
    [62, 84],
    [108, 62],
    [86, 40],
    [144, 58],
  ];
  apples.slice(0, fruits).forEach(([x, y]) => {
    parts.push(circle(x, y, 6, C.fruit), circle(x - 2, y - 2, 2, C.fruitShine));
  });
  return parts;
}
