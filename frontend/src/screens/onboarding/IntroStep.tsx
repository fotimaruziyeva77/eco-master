import { ArrowRight, BellRing } from "lucide-react";
import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";

import { api } from "../../api/client";
import { Toggle } from "../../components/ui";
import { Emoji } from "../../components/Emoji";
import { useUser } from "../../state/user";
import { haptic, requestWriteAccess } from "../../telegram";
import type { LegalDocumentKind } from "../PrivacyScreen";

const SLIDES = [
  { icon: "♻️", title: "onboarding.intro.slide1Title", text: "onboarding.intro.slide1Text" },
  { icon: "🎮", title: "onboarding.intro.slide2Title", text: "onboarding.intro.slide2Text" },
  { icon: "🏆", title: "onboarding.intro.slide3Title", text: "onboarding.intro.slide3Text" },
];

export function IntroStep({ onOpenDocument }: { onOpenDocument: (kind: LegalDocumentKind) => void }) {
  const { t } = useTranslation();
  const { user, setUser } = useUser();
  const [slide, setSlide] = useState(0);
  const [reminders, setReminders] = useState(true);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const isLast = slide === SLIDES.length - 1;

  async function finish() {
    if (busy) return;
    setBusy(true);
    setFailed(false);
    try {
      // Reminders need the user's permission for the bot to write (TZ 8.1). Declining is fine.
      if (reminders && !user.write_access && (await requestWriteAccess())) {
        await api.setWriteAccess(true);
      }
      await api.updateMe({ reminders_enabled: reminders });
      const done = await api.onboardingComplete();
      haptic.success();
      setUser(done);
    } catch {
      setFailed(true);
      setBusy(false);
    }
  }

  const current = SLIDES[slide];
  return (
    <section className="intro">
      <div className="intro__slide" key={slide}>
        <div className="intro__art" aria-hidden="true">
          <Emoji char={current.icon} />
        </div>
        <h1>{t(current.title)}</h1>
        <p className="hint">{t(current.text)}</p>
      </div>

      <div className="dots dots--center" aria-hidden="true" style={{ margin: "16px 0" }}>
        {SLIDES.map((s, i) => (
          <span key={s.title} className={i === slide ? "dot is-active" : "dot"} />
        ))}
      </div>

      {isLast && (
        <div className="card card--soft row" style={{ marginBottom: 16, gap: 12 }}>
          <span className="icon-tile icon-tile--amber" aria-hidden="true">
            <BellRing size={20} />
          </span>
          <span className="list-row__text">
            <strong>{t("onboarding.intro.remindersTitle")}</strong>
            <span className="hint small">{t("onboarding.intro.remindersText")}</span>
          </span>
          <Toggle checked={reminders} onChange={setReminders} label={t("onboarding.intro.remindersTitle")} />
        </div>
      )}

      {failed && (
        <p className="error-text" role="alert">
          {t("errors.network")}
        </p>
      )}

      <div className="stack">
        <button
          type="button"
          className="btn btn--block"
          disabled={busy}
          onClick={() => (isLast ? void finish() : setSlide(slide + 1))}
        >
          {isLast ? t("onboarding.intro.start") : t("onboarding.intro.next")} <ArrowRight size={20} />
        </button>
        {!isLast && (
          <button type="button" className="link-button" disabled={busy} onClick={() => void finish()}>
            {t("onboarding.intro.skip")}
          </button>
        )}
      </div>

      <p className="hint small consent" style={{ marginTop: 12 }}>
        <Trans
          i18nKey="onboarding.intro.consent"
          components={{
            policy: <button type="button" className="link-inline" onClick={() => onOpenDocument("privacy")} />,
            terms: <button type="button" className="link-inline" onClick={() => onOpenDocument("terms")} />,
          }}
        />
      </p>
    </section>
  );
}
