import { useTranslation } from "react-i18next";

import mark from "../assets/brand/eco-master-mark.webp";

export function LoadingScreen() {
  const { t } = useTranslation();
  return (
    <main className="screen screen--center" aria-busy="true">
      <img className="brand-mark" src={mark} alt="Eco-Master" />
      <div className="spinner" aria-hidden="true" style={{ marginTop: 12 }} />
      <p className="hint">{t("common.loading")}</p>
    </main>
  );
}
