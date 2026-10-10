import { useTranslation } from "react-i18next";

import { useBack } from "../hooks/useBack";
import { insideTelegram, useTelegramBackButton } from "../telegram";

const SECTIONS = ["collect", "notCollect", "why", "who", "delete", "contact"] as const;

/** Draft privacy notice (TZ 11.2). The final text comes after the legal review (TZ 11.4). */
export function PrivacyContent({ onBack }: { onBack: () => void }) {
  const { t } = useTranslation();
  return (
    <article className="privacy">
      {!insideTelegram() && (
        <button className="link-button" type="button" onClick={onBack}>
          ← {t("common.back")}
        </button>
      )}
      <h1>{t("privacy.title")}</h1>
      <p className="note">{t("privacy.draft")}</p>
      {SECTIONS.map((section) => (
        <section key={section} className="card">
          <h2>{t(`privacy.${section}Title`)}</h2>
          <p>{t(`privacy.${section}Text`)}</p>
        </section>
      ))}
    </article>
  );
}

export function PrivacyScreen() {
  const back = useBack("/profile");
  useTelegramBackButton(back);
  return (
    <main className="screen">
      <PrivacyContent onBack={back} />
    </main>
  );
}
