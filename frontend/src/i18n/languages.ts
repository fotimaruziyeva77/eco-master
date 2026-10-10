export const LANGUAGES = ["uz", "ru", "en"] as const;
export type Language = (typeof LANGUAGES)[number];
export const DEFAULT_LANGUAGE: Language = "uz";

export const LANGUAGE_NAMES: Record<Language, string> = {
  uz: "O'zbekcha",
  ru: "Русский",
  en: "English",
};

/** Same rule as the backend (TZ 6): uz/ru/en map to themselves, everything else to Uzbek. */
export function pickLanguage(code: string | null | undefined): Language {
  if (!code) return DEFAULT_LANGUAGE;
  const base = code.toLowerCase().replace("_", "-").split("-")[0];
  return (LANGUAGES as readonly string[]).includes(base) ? (base as Language) : DEFAULT_LANGUAGE;
}
