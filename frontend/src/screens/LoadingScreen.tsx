import { useTranslation } from "react-i18next";

export function LoadingScreen() {
  const { t } = useTranslation();
  return (
    <main className="screen screen--center" aria-busy="true">
      <div className="spinner" aria-hidden="true" />
      <p className="hint">{t("common.loading")}</p>
    </main>
  );
}
