import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import type { User } from "../../api/client";
import { useUser } from "../../state/user";
import { insideTelegram, useTelegramBackButton } from "../../telegram";
import { PrivacyContent } from "../PrivacyScreen";
import { IntroStep } from "./IntroStep";
import { LanguageStep } from "./LanguageStep";
import { NicknameStep } from "./NicknameStep";
import { PathStep } from "./PathStep";

const STEPS = ["language", "path", "nickname", "intro"] as const;
type Step = (typeof STEPS)[number];

function savedStep(user: User): Step {
  return user.onboarding_step === "done" ? "intro" : user.onboarding_step;
}

/** TZ 8.1: language → path → nickname → intro. Resumes at the step saved on the server. */
export function OnboardingFlow() {
  const { t } = useTranslation();
  const { user } = useUser();
  const [step, setStep] = useState<Step>(() => savedStep(user));
  const [privacyOpen, setPrivacyOpen] = useState(false);

  const index = STEPS.indexOf(step);
  const back = useMemo(() => {
    if (privacyOpen) return () => setPrivacyOpen(false);
    return index > 0 ? () => setStep(STEPS[index - 1]) : undefined;
  }, [privacyOpen, index]);
  useTelegramBackButton(back);

  if (privacyOpen) {
    return (
      <main className="screen">
        {!insideTelegram() && (
          <button type="button" className="link-button" onClick={() => setPrivacyOpen(false)}>
            ← {t("common.back")}
          </button>
        )}
        <PrivacyContent />
      </main>
    );
  }

  return (
    <main className="screen onboarding">
      <div className="onboarding__progress">
        <div className="dots" aria-hidden="true">
          {STEPS.map((s, i) => (
            <span key={s} className={i <= index ? "dot is-active" : "dot"} />
          ))}
        </div>
        <span className="hint">
          {t("onboarding.step", { current: index + 1, total: STEPS.length })}
        </span>
      </div>
      {step === "language" && <LanguageStep onDone={() => setStep("path")} />}
      {step === "path" && <PathStep onDone={() => setStep("nickname")} />}
      {step === "nickname" && <NicknameStep onDone={() => setStep("intro")} />}
      {step === "intro" && <IntroStep onOpenPrivacy={() => setPrivacyOpen(true)} />}
    </main>
  );
}
