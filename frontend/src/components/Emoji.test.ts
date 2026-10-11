import { describe, expect, it } from "vitest";

import { emojiSrc } from "./Emoji";

const SOURCES = import.meta.glob(["../**/*.{ts,tsx}", "!../**/*.test.ts", "!../api/schema.ts"], {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;
// A string literal that is one emoji (with joiners, variation selectors, keycaps).
const EMOJI_LITERAL = /["'`](\p{Extended_Pictographic}[\p{Extended_Pictographic}\u200d\ufe0f\u20e3]*)["'`]/gu;
// The generated pictures (lazy: only their names are needed).
const PICTURES = new Set(
  Object.keys(import.meta.glob("../../public/emoji/*.svg")).map((path) => path.replace("../../public", "")),
);

describe("emoji pictures", () => {
  it("are named by code points, without variation selectors", () => {
    expect(emojiSrc("🔥")).toBe("/emoji/1f525.svg");
    expect(emojiSrc("♻️")).toBe("/emoji/267b.svg");
    expect(emojiSrc("👩‍🏫")).toBe("/emoji/1f469-200d-1f3eb.svg");
    expect(emojiSrc("")).toBeNull();
  });

  // Every emoji the code shows must exist in the set (scripts/emoji.mjs, run before the tests);
  // otherwise it would fall back to the phone's own emoji.
  it("exist for every emoji the code uses", () => {
    const used = new Set<string>();
    for (const source of Object.values(SOURCES)) {
      for (const match of source.matchAll(EMOJI_LITERAL)) used.add(match[1]);
    }
    expect(used.size).toBeGreaterThan(20);
    const missing = [...used].filter((char) => !PICTURES.has(emojiSrc(char) ?? ""));
    expect(missing).toEqual([]);
  });
});
