import { useTranslation } from "react-i18next";

import { ApiError } from "../api/client";

export { SubpageHeader } from "./ui";

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
        <button className="btn btn--soft btn--sm" type="button" onClick={onRetry}>
          {t("common.retry")}
        </button>
      )}
    </div>
  );
}
