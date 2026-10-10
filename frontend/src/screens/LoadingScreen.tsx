import { useTranslation } from "react-i18next";

export function LoadingScreen() {
  const { t } = useTranslation();
  return (
    <main className="screen screen--center" aria-busy="true">
      <span className="logo" style={{ width: 64, height: 64, fontSize: 34, borderRadius: 20 }} aria-hidden="true">
        🌱
      </span>
      <div className="spinner" aria-hidden="true" style={{ marginTop: 12 }} />
      <p className="hint">{t("common.loading")}</p>
    </main>
  );
}
