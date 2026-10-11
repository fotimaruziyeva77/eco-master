import { useTranslation } from "react-i18next";

import mark from "../assets/brand/eco-master-mark.webp";
import { telegramAppLink } from "../telegram";

/** Shown when the link is opened in a normal browser: there is no initData to log in with (QM-21). */
export function OpenInTelegramScreen() {
  const { t } = useTranslation();
  const link = telegramAppLink();
  return (
    <main className="screen screen--center">
      <img className="brand-mark" src={mark} alt="Eco-Master" />
      <h1>{t("openInTelegram.title")}</h1>
      <p className="hint">{t("openInTelegram.text")}</p>
      {link && (
        <a className="btn" href={link} style={{ marginTop: 12 }}>
          {t("openInTelegram.button")}
        </a>
      )}
    </main>
  );
}
