import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { DEFAULT_LANGUAGE, LANGUAGES, type Language } from "./languages";
import uz from "./locales/uz.json";

// Uzbek is the default and the fallback, so it ships with the app; Russian and English are
// fetched only for those who use them — a smaller first load on slow networks (TZ 13).
const LOADERS: Record<Exclude<Language, "uz">, () => Promise<{ default: object }>> = {
  ru: () => import("./locales/ru.json"),
  en: () => import("./locales/en.json"),
};

export async function loadLanguage(language: Language): Promise<void> {
  if (language === "uz" || i18n.hasResourceBundle(language, "translation")) return;
  const bundle = await LOADERS[language]();
  i18n.addResourceBundle(language, "translation", bundle.default, true, true);
}

/** Switch the interface language, loading its texts first. */
export async function changeLanguage(language: Language): Promise<void> {
  await loadLanguage(language);
  await i18n.changeLanguage(language);
}

/** Every language at once: the admin preview shows all three. */
export async function loadAllLanguages(): Promise<void> {
  await Promise.all(LANGUAGES.map(loadLanguage));
}

export async function initI18n(language: Language): Promise<typeof i18n> {
  await i18n.use(initReactI18next).init({
    resources: { uz: { translation: uz } },
    lng: DEFAULT_LANGUAGE,
    fallbackLng: DEFAULT_LANGUAGE,
    interpolation: { escapeValue: false },
    returnNull: false,
  });
  document.documentElement.lang = DEFAULT_LANGUAGE;
  i18n.on("languageChanged", (lng) => {
    document.documentElement.lang = lng;
  });
  try {
    await changeLanguage(language);
  } catch {
    // No connection for the language file: start in Uzbek rather than not at all.
  }
  return i18n;
}

export default i18n;
