import type { Language } from "./languages";

// Browsers' Uzbek date data is patchy (some print "M10 19"), so Uzbek dates are made here.
const UZ_MONTHS = [
  "yanvar",
  "fevral",
  "mart",
  "aprel",
  "may",
  "iyun",
  "iyul",
  "avgust",
  "sentabr",
  "oktabr",
  "noyabr",
  "dekabr",
];
const UZ_WEEKDAYS = ["yakshanba", "dushanba", "seshanba", "chorshanba", "payshanba", "juma", "shanba"];

/** "19-oktabr" / "19 октября" / "19 October", with the weekday in front if asked. */
export function formatDay(day: Date, language: Language | string, weekday = false): string {
  if (language === "uz") {
    const date = `${day.getDate()}-${UZ_MONTHS[day.getMonth()]}`;
    return weekday ? `${UZ_WEEKDAYS[day.getDay()]}, ${date}` : date;
  }
  return day.toLocaleDateString(language, {
    day: "numeric",
    month: "long",
    ...(weekday ? { weekday: "long" as const } : {}),
  });
}
