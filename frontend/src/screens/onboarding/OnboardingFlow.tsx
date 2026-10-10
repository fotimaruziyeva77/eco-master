import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type User } from "../../api/client";
import { useUser } from "../../state/user";
import { insideTelegram, useTelegramBackButton } from "../../telegram";
import { LegalContent, type LegalDocumentKind } from "../PrivacyScreen";
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
  const { user, setUser } = useUser();
  // A moderator reset the nickname of someone who had finished onboarding.
  const nicknameReset = user.onboarded_at != null && user.onboarding_step === "nickname";
  const [step, setStep] = useState<Step>(() => savedStep(user));
  const [document, setDocument] = useState<LegalDocumentKind | null>(null);

  const index = STEPS.indexOf(step);
  const back = useMemo(() => {
    if (document) return () => setDocument(null);
    return index > 0 ? () => setStep(STEPS[index - 1]) : undefined;
  }, [document, index]);
  useTelegramBackButton(back);

  if (nicknameReset) {
    return (
      <main className="screen onboarding">
        <NicknameStep
          notice={t("onboarding.nicknameReset")}
          onDone={() => void api.onboardingComplete().then(setUser)}
        />
      </main>
    );
  }

  if (document) {
    return (
      <main className="screen">
        {!insideTelegram() && (
          <button type="button" className="link-button" onClick={() => setDocument(null)}>
            ← {t("common.back")}
          </button>
        )}
        <LegalContent kind={document} />
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
      {step === "intro" && <IntroStep onOpenDocument={setDocument} />}
    </main>
  );
}
