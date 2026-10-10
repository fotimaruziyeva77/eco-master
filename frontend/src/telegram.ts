import { useEffect } from "react";
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

function supports(version: string): boolean {
  return Boolean(tg?.initData) && tg!.isVersionAtLeast(version);
}

export function setupTelegramUi(): void {
  if (!tg) return;
  tg.ready();
  tg.expand();
  const applyScheme = () =>
    document.documentElement.classList.toggle("tg-dark", tg!.colorScheme === "dark");
  applyScheme();
  tg.onEvent("themeChanged", applyScheme);
}

/** t.me link that opens the Mini App inside Telegram, or null if the bot is not configured. */
export function telegramAppLink(): string | null {
  const bot = import.meta.env.VITE_BOT_USERNAME;
  if (!bot) return null;
  const app = import.meta.env.VITE_WEBAPP_SHORT_NAME || "app";
  return `https://t.me/${bot}/${app}`;
}

export const haptic = {
  success() {
    if (supports("6.1")) tg!.HapticFeedback.notificationOccurred("success");
  },
  error() {
    if (supports("6.1")) tg!.HapticFeedback.notificationOccurred("error");
  },
  tap() {
    if (supports("6.1")) tg!.HapticFeedback.selectionChanged();
  },
};

/** Ask whether the bot may message the user (reminders). Resolves false where unsupported. */
export function requestWriteAccess(): Promise<boolean> {
  if (!supports("6.9")) return Promise.resolve(false);
  return new Promise((resolve) => tg!.requestWriteAccess((granted) => resolve(granted)));
}

/** True when running inside Telegram (as opposed to a browser in development). */
export function insideTelegram(): boolean {
  return Boolean(tg?.initData);
}

/** Show Telegram's native back button while the calling screen is mounted. */
export function useTelegramBackButton(onBack: (() => void) | undefined): void {
  useEffect(() => {
    if (!onBack || !supports("6.1")) return;
    tg!.BackButton.onClick(onBack);
    tg!.BackButton.show();
    return () => {
      tg!.BackButton.offClick(onBack);
      tg!.BackButton.hide();
    };
  }, [onBack]);
}

/** Open an external link in the browser (inside Telegram) or a new tab (dev). */
export function openExternal(url: string): void {
  if (tg?.initData) tg.openLink(url);
  else window.open(url, "_blank", "noopener");
}
