import { useEffect } from "react";
import type { WebApp } from "telegram-web-app";

/** Telegram Mini App bridge; undefined if telegram-web-app.js failed to load. */
export const tg: WebApp | undefined = window.Telegram?.WebApp;

/** Signed launch data. Empty when the page is opened outside Telegram. */
export function getInitData(): string {
  return tg?.initData ?? "";
}

/** The startapp parameter of the link that opened the app (e.g. "market"). */
export function startParam(): string | undefined {
  return tg?.initDataUnsafe?.start_param;
}

/** Language of the Telegram client — only a hint for the UI before login. */
export function telegramLanguageCode(): string | undefined {
  return tg?.initDataUnsafe?.user?.language_code;
}

function supports(version: string): boolean {
  return Boolean(tg?.initData) && tg!.isVersionAtLeast(version);
}

/** Follow Telegram's light/dark theme; in a normal browser follow the system setting. */
export function setupTelegramUi(): void {
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  const apply = () => {
    const dark = tg?.initData ? tg.colorScheme === "dark" : media.matches;
    document.documentElement.classList.toggle("theme-dark", dark);
  };
  apply();
  media.addEventListener("change", apply);
  if (!tg) return;
  tg.ready();
  tg.expand();
  tg.onEvent("themeChanged", apply);
}

/** t.me link that opens the Mini App inside Telegram, or null if the bot is not configured. */
export function telegramAppLink(): string | null {
  const bot = import.meta.env.VITE_BOT_USERNAME;
  if (!bot) return null;
  const app = import.meta.env.VITE_WEBAPP_SHORT_NAME || "app";
  return `https://t.me/${bot}/${app}`;
}

/** Chat with the bot (feedback, /start), or null if the bot is not configured. */
export function botChatLink(): string | null {
  const bot = import.meta.env.VITE_BOT_USERNAME;
  return bot ? `https://t.me/${bot}` : null;
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

/**
 * Stop a downward swipe from closing the Mini App while the calling screen is mounted
 * (TZ 8.4: games must not close on an accidental swipe).
 */
export function useNoVerticalSwipes(): void {
  useEffect(() => {
    if (!supports("7.7")) return;
    tg!.disableVerticalSwipes();
    return () => tg!.enableVerticalSwipes();
  }, []);
}

/** Open an external link in the browser (inside Telegram) or a new tab (dev). */
export function openExternal(url: string): void {
  if (tg?.initData) tg.openLink(url);
  else window.open(url, "_blank", "noopener");
}

/** Open a t.me link inside Telegram itself (a new tab outside Telegram). */
export function openTelegramLink(url: string): void {
  if (tg?.initData) tg.openTelegramLink(url);
  else window.open(url, "_blank", "noopener");
}

type Shareable = {
  text: string;
  url: string;
  prepared_message_id?: string | null;
  inline_query?: string | null;
};

/**
 * Open Telegram's chat picker with a ready message (TZ 8.11, QM-16). Telegram 8.0+ sends the
 * prepared message with an "Open the app" button; older clients go through the bot's inline
 * mode; without either, Telegram's share link carries the text and the app link.
 */
export async function shareToChat(item: Shareable): Promise<void> {
  if (item.prepared_message_id && supports("8.0")) {
    tg!.shareMessage(item.prepared_message_id);
    return;
  }
  if (item.inline_query && supports("6.7")) {
    tg!.switchInlineQuery(item.inline_query, ["users", "groups"]);
    return;
  }
  const link = `https://t.me/share/url?url=${encodeURIComponent(item.url)}&text=${encodeURIComponent(item.text)}`;
  if (insideTelegram() || !navigator.share) {
    openTelegramLink(link);
    return;
  }
  try {
    await navigator.share({ text: item.text, url: item.url });
  } catch {
    // The share sheet was closed.
  }
}
