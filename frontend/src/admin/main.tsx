import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "@fontsource-variable/plus-jakarta-sans";
import { initI18n } from "../i18n";
import "../styles.css";
import "./admin.css";
import { AdminApp } from "./AdminApp";

// The content preview uses the Mini App's own translations for its headings.
initI18n("uz");

const dark = window.matchMedia("(prefers-color-scheme: dark)");
const applyTheme = () => document.documentElement.classList.toggle("theme-dark", dark.matches);
applyTheme();
dark.addEventListener("change", applyTheme);

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AdminApp />
  </StrictMode>,
);
