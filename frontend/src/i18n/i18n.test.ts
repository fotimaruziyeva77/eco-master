import { describe, expect, it } from "vitest";

import { LANGUAGES, pickLanguage } from "./languages";
import en from "./locales/en.json";
import ru from "./locales/ru.json";
import uz from "./locales/uz.json";

const LOCALES = { uz, ru, en } as const;
const PLURAL_SUFFIX = /_(zero|one|two|few|many|other)$/;

const SOURCES = import.meta.glob(["../**/*.{ts,tsx}", "!../**/*.test.ts", "!../api/schema.ts"], {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;
const USED_KEY = /\bt\(\s*["']([A-Za-z0-9_.]+)["']|i18nKey=["']([A-Za-z0-9_.]+)["']/g;

type Tree = { [key: string]: string | Tree };

function flatten(tree: Tree, prefix = ""): Map<string, string> {
  const out = new Map<string, string>();
  for (const [key, value] of Object.entries(tree)) {
    const path = prefix ? `${prefix}.${key}` : key;
    if (typeof value === "string") out.set(path, value);
    else for (const [k, v] of flatten(value, path)) out.set(k, v);
  }
  return out;
}

function baseKeys(keys: Iterable<string>): Set<string> {
  return new Set([...keys].map((key) => key.replace(PLURAL_SUFFIX, "")));
}

describe("locale files (QM-04)", () => {
  const flat = Object.fromEntries(
    LANGUAGES.map((lang) => [lang, flatten(LOCALES[lang] as Tree)]),
  ) as Record<(typeof LANGUAGES)[number], Map<string, string>>;

  it("have the same keys in every language", () => {
    const reference = [...baseKeys(flat.uz.keys())].sort();
    for (const lang of LANGUAGES) {
      expect([...baseKeys(flat[lang].keys())].sort(), lang).toEqual(reference);
    }
  });

  it("have no empty strings", () => {
    for (const lang of LANGUAGES) {
      for (const [key, value] of flat[lang]) {
        expect(value.trim(), `${lang}:${key}`).not.toBe("");
      }
    }
  });

  it("define every plural form the language needs", () => {
    for (const lang of LANGUAGES) {
      const categories = new Intl.PluralRules(lang).resolvedOptions().pluralCategories;
      const pluralBases = new Set(
        [...flat[lang].keys()].filter((k) => PLURAL_SUFFIX.test(k)).map((k) => k.replace(PLURAL_SUFFIX, "")),
      );
      for (const base of pluralBases) {
        for (const category of categories) {
          expect(flat[lang].has(`${base}_${category}`), `${lang}:${base}_${category}`).toBe(true);
        }
      }
    }
  });

  // A key missing from the files would show up on screen as is, e.g. "home.title".
  // Keys built at run time (`levels.${code}`) are not covered here.
  it("contain every key the code uses", () => {
    const keys = [...flat.uz.keys()];
    const missing: string[] = [];
    let checked = 0;
    for (const [file, source] of Object.entries(SOURCES)) {
      for (const match of source.matchAll(USED_KEY)) {
        const key = match[1] ?? match[2];
        const known =
          flat.uz.has(key) || keys.some((k) => k.startsWith(`${key}.`) || k.startsWith(`${key}_`));
        if (!known) missing.push(`${file}: ${key}`);
        checked += 1;
      }
    }
    expect(missing).toEqual([]);
    expect(checked).toBeGreaterThan(200);
  });
});

describe("pickLanguage (QM-02)", () => {
  it.each([
    ["uz", "uz"],
    ["ru", "ru"],
    ["en", "en"],
    ["ru-RU", "ru"],
    ["en_US", "en"],
    ["kk", "uz"],
    ["de", "uz"],
    [undefined, "uz"],
  ])("%s -> %s", (code, expected) => {
    expect(pickLanguage(code)).toBe(expected);
  });
});
