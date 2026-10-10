import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { trackError } from "../analytics";

type Props = { messageKey: string; onRetry: () => void };

export function ErrorScreen({ messageKey, onRetry }: Props) {
  const { t } = useTranslation();
  useEffect(() => trackError(messageKey.replace("errors.", "screen_")), [messageKey]);
  return (
    <main className="screen screen--center" role="alert">
      <div className="intro__art" aria-hidden="true">
        🍂
      </div>
      <h1>{t("errors.title")}</h1>
      <p className="hint">{t(messageKey)}</p>
      <button className="btn" type="button" onClick={onRetry} style={{ marginTop: 12 }}>
        {t("common.retry")}
      </button>
    </main>
  );
}
