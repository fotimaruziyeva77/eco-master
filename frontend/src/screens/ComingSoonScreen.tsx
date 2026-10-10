import { useTranslation } from "react-i18next";

export function ComingSoonScreen({ icon }: { icon: string }) {
  const { t } = useTranslation();
  return (
    <main className="screen screen--with-nav screen--center">
      <div className="emoji" aria-hidden="true">
        {icon}
      </div>
      <h1>{t("soon.title")}</h1>
      <p className="hint">{t("soon.text")}</p>
    </main>
  );
}
