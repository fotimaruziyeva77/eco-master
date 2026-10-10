import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { watchErrors } from "./analytics";
import App from "./App";
import { initI18n } from "./i18n";
import { pickLanguage } from "./i18n/languages";
import "@fontsource-variable/plus-jakarta-sans";
import "./styles.css";
import { telegramLanguageCode } from "./telegram";

watchErrors();

// Until the server tells us the saved language, use the Telegram client's language.
void initI18n(pickLanguage(telegramLanguageCode() ?? navigator.language)).then(() =>
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  ),
);
