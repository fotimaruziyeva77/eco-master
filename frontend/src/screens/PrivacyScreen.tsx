import { ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";

import { SubpageHeader } from "../components/ui";
import { useBack } from "../hooks/useBack";

const SECTIONS = ["collect", "notCollect", "why", "who", "delete", "contact"] as const;

/** Draft privacy notice (TZ 11.2). The final text comes after the legal review (TZ 11.4). */
export function PrivacyContent() {
  const { t } = useTranslation();
  return (
    <article className="stack">
      <h1 className="row">
        <ShieldCheck size={26} aria-hidden="true" /> {t("privacy.title")}
      </h1>
      <p className="note">{t("privacy.draft")}</p>
      {SECTIONS.map((section) => (
        <section key={section} className="card stack" style={{ gap: 6 }}>
          <h3>{t(`privacy.${section}Title`)}</h3>
          <p className="text-2">{t(`privacy.${section}Text`)}</p>
        </section>
      ))}
    </article>
  );
}

export function PrivacyScreen() {
  const { t } = useTranslation();
  const back = useBack("/profile");
  return (
    <main className="screen">
      <SubpageHeader onBack={back} title={t("profile.privacy")} />
      <PrivacyContent />
    </main>
  );
}
