import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { DEFAULT_LANGUAGE, type Language } from "./languages";
import en from "./locales/en.json";
import ru from "./locales/ru.json";
import uz from "./locales/uz.json";

export const resources = {
  uz: { translation: uz },
  ru: { translation: ru },
  en: { translation: en },
} as const;

export function initI18n(language: Language): typeof i18n {
  void i18n.use(initReactI18next).init({
    resources,
    lng: language,
    fallbackLng: DEFAULT_LANGUAGE,
    interpolation: { escapeValue: false },
    returnNull: false,
  });
  document.documentElement.lang = language;
  i18n.on("languageChanged", (lng) => {
    document.documentElement.lang = lng;
  });
  return i18n;
}

export default i18n;
