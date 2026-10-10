import { useTranslation } from "react-i18next";

import { telegramAppLink } from "../telegram";

/** Shown when the link is opened in a normal browser: there is no initData to log in with (QM-21). */
export function OpenInTelegramScreen() {
  const { t } = useTranslation();
  const link = telegramAppLink();
  return (
    <main className="screen screen--center">
      <div className="emoji" aria-hidden="true">
        🌱
      </div>
      <h1>{t("openInTelegram.title")}</h1>
      <p className="hint">{t("openInTelegram.text")}</p>
      {link && (
        <a className="button" href={link}>
          {t("openInTelegram.button")}
        </a>
      )}
    </main>
  );
}
