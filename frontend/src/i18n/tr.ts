import { useCallback } from "react";
import { useTranslation } from "react-i18next";

import { DEFAULT_LANGUAGE } from "./languages";

type Localized = { [language: string]: unknown } | null | undefined;

/**
 * Pick the current language from a server content field ({"uz": ..., "ru": ..., "en": ...}).
 * Falls back to Uzbek, so a missing translation never shows an empty screen.
 */
export function useTr() {
  const { i18n } = useTranslation();
  const language = i18n.language;
  return useCallback(
    <T = string>(value: Localized): T | undefined => {
      if (!value) return undefined;
      return (value[language] ?? value[DEFAULT_LANGUAGE] ?? Object.values(value)[0]) as
        | T
        | undefined;
    },
    [language],
  );
}
