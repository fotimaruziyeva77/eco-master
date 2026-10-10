import type { WebApp } from "telegram-web-app";

/** Telegram Mini App bridge; undefined if telegram-web-app.js failed to load. */
export const tg: WebApp | undefined = window.Telegram?.WebApp;

/** Signed launch data. Empty when the page is opened outside Telegram. */
export function getInitData(): string {
  return tg?.initData ?? "";
}

/** Language of the Telegram client — only a hint for the UI before login. */
export function telegramLanguageCode(): string | undefined {
  return tg?.initDataUnsafe?.user?.language_code;
}

export function setupTelegramUi(): void {
  if (!tg) return;
  tg.ready();
  tg.expand();
  document.documentElement.classList.toggle("tg-dark", tg.colorScheme === "dark");
  tg.onEvent("themeChanged", () => {
    document.documentElement.classList.toggle("tg-dark", tg.colorScheme === "dark");
  });
}

/** t.me link that opens the Mini App inside Telegram, or null if the bot is not configured. */
export function telegramAppLink(): string | null {
  const bot = import.meta.env.VITE_BOT_USERNAME;
  if (!bot) return null;
  const app = import.meta.env.VITE_WEBAPP_SHORT_NAME || "app";
  return `https://t.me/${bot}/${app}`;
}
