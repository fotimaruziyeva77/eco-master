import { useTranslation } from "react-i18next";

type Props = { messageKey: string; onRetry: () => void };

export function ErrorScreen({ messageKey, onRetry }: Props) {
  const { t } = useTranslation();
  return (
    <main className="screen screen--center" role="alert">
      <div className="emoji" aria-hidden="true">
        🍂
      </div>
      <h1>{t("errors.title")}</h1>
      <p className="hint">{t(messageKey)}</p>
      <button className="button" type="button" onClick={onRetry}>
        {t("common.retry")}
      </button>
    </main>
  );
}
