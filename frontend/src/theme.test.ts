import { describe, expect, it } from "vitest";

import css from "./tokens.css?raw";

/** Text contrast of the design tokens, light and dark (TZ 12, QM-20: WCAG AA 4.5:1). */

type Rgba = [number, number, number, number];

function block(selector: string): Record<string, string> {
  const start = css.indexOf(`${selector} {`);
  const body = css.slice(start, css.indexOf("}", start));
  return Object.fromEntries([...body.matchAll(/--([\w-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2].trim()]));
}

const LIGHT = block(":root");
const DARK = { ...LIGHT, ...block(":root.theme-dark") };

function parse(value: string): Rgba {
  const hex = value.match(/^#([0-9a-f]{6})$/i);
  if (hex) {
    const n = parseInt(hex[1], 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255, 1];
  }
  const rgba = value.match(/^rgba?\(([^)]+)\)$/);
  if (rgba) {
    const [r, g, b, a = "1"] = rgba[1].split(",").map((p) => p.trim());
    return [Number(r), Number(g), Number(b), Number(a)];
  }
  throw new Error(`unsupported colour ${value}`);
}

/** A see-through colour as it looks on top of `under`. */
function over([r, g, b, a]: Rgba, [br, bg, bb]: Rgba): Rgba {
  return [r * a + br * (1 - a), g * a + bg * (1 - a), b * a + bb * (1 - a), 1];
}

function luminance([r, g, b]: Rgba): number {
  const channel = (c: number) => {
    const s = c / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

function contrast(a: Rgba, b: Rgba): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// [text, background, surface under a see-through background]
const PAIRS: [string, string, string?][] = [
  ["text", "canvas"],
  ["text", "card"],
  ["text-2", "card"],
  ["text-2", "canvas"],
  ["hint", "card"],
  ["hint", "canvas"],
  ["on-primary", "primary-strong"],
  ["on-primary-soft", "card"],
  ["on-primary-soft", "canvas"],
  ["on-primary-soft", "primary-soft", "card"],
  ["on-primary-soft", "primary-soft-2", "card"],
  ["on-amber-soft", "amber-soft", "card"],
  ["on-sky-soft", "sky-soft", "card"],
  ["on-danger-soft", "danger-soft", "card"],
  ["danger", "card"],
  ["danger", "canvas"],
];

describe.each([
  ["light", LIGHT],
  ["dark", DARK],
])("%s theme", (_name, tokens) => {
  const colour = (name: string) => parse(tokens[name]);

  it.each(PAIRS)("%s on %s is at least 4.5:1", (text, background, surface) => {
    const under = surface ? colour(surface) : parse("#ffffff");
    const bg = over(colour(background), under);
    const fg = over(colour(text), bg);
    expect(contrast(fg, bg)).toBeGreaterThanOrEqual(4.5);
  });

  it("white text on the hero card gradient", () => {
    for (const stop of ["hero-from", "hero-to"]) {
      expect(contrast(parse("#ffffff"), colour(stop))).toBeGreaterThanOrEqual(4.5);
    }
  });
});
