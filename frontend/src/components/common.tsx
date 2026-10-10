import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { ApiError } from "../api/client";
import { insideTelegram, useTelegramBackButton } from "../telegram";

export function InlineLoading() {
  const { t } = useTranslation();
  return (
    <div className="inline-state" aria-busy="true">
      <div className="spinner" aria-hidden="true" />
      <span className="hint">{t("common.loading")}</span>
    </div>
  );
}

export function InlineError({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const { t } = useTranslation();
  const key =
    error instanceof ApiError
      ? error.status === 404
        ? "errors.notFound"
        : "errors.unknown"
      : "errors.network";
  return (
    <div className="inline-state" role="alert">
      <p className="hint">{t(key)}</p>
      {key !== "errors.notFound" && (
        <button className="button button--secondary" type="button" onClick={onRetry}>
          {t("common.retry")}
        </button>
      )}
    </div>
  );
}

/** Header of a nested screen: Telegram's own back button inside Telegram, a link in a browser. */
export function SubpageHeader({ title, onBack }: { title?: ReactNode; onBack: () => void }) {
  const { t } = useTranslation();
  useTelegramBackButton(onBack);
  return (
    <header className="subpage-header">
      {!insideTelegram() && (
        <button className="link-button" type="button" onClick={onBack}>
          ← {t("common.back")}
        </button>
      )}
      {title && <h1>{title}</h1>}
    </header>
  );
}
