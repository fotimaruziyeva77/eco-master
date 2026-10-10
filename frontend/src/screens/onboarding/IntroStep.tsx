import { useState } from "react";
import { Trans, useTranslation } from "react-i18next";

import { api } from "../../api/client";
import { useUser } from "../../state/user";
import { haptic, requestWriteAccess } from "../../telegram";

const SLIDES = [
  { icon: "♻️", title: "onboarding.intro.slide1Title", text: "onboarding.intro.slide1Text" },
  { icon: "🎮", title: "onboarding.intro.slide2Title", text: "onboarding.intro.slide2Text" },
  { icon: "🏆", title: "onboarding.intro.slide3Title", text: "onboarding.intro.slide3Text" },
];

export function IntroStep({ onOpenPrivacy }: { onOpenPrivacy: () => void }) {
  const { t } = useTranslation();
  const { user, setUser } = useUser();
  const [slide, setSlide] = useState(0);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const isLast = slide === SLIDES.length - 1;

  async function finish() {
    if (busy) return;
    setBusy(true);
    setFailed(false);
    try {
      // Reminders need the user's permission for the bot to write (TZ 8.1). Declining is fine.
      if (!user.write_access && (await requestWriteAccess())) {
        await api.setWriteAccess(true);
      }
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
        <div className="emoji emoji--large" aria-hidden="true">
          {current.icon}
        </div>
        <h1>{t(current.title)}</h1>
        <p className="hint">{t(current.text)}</p>
      </div>

      <div className="dots dots--center" aria-hidden="true">
        {SLIDES.map((s, i) => (
          <span key={s.title} className={i === slide ? "dot is-active" : "dot"} />
        ))}
      </div>

      {failed && (
        <p className="error-text" role="alert">
          {t("errors.network")}
        </p>
      )}

      <div className="intro__actions">
        <button
          type="button"
          className="button button--block"
          disabled={busy}
          onClick={() => (isLast ? void finish() : setSlide(slide + 1))}
        >
          {isLast ? t("onboarding.intro.start") : t("onboarding.intro.next")}
        </button>
        {!isLast && (
          <button type="button" className="link-button" disabled={busy} onClick={() => void finish()}>
            {t("onboarding.intro.skip")}
          </button>
        )}
      </div>

      <p className="hint small consent">
        <Trans
          i18nKey="onboarding.intro.consent"
          components={{ policy: <button type="button" className="link-inline" onClick={onOpenPrivacy} /> }}
        />
      </p>
    </section>
  );
}
