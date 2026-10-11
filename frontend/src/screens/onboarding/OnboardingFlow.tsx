import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import type { User } from "../../api/client";
import { useUser } from "../../state/user";
import { insideTelegram, useTelegramBackButton } from "../../telegram";
import { LegalContent, type LegalDocumentKind } from "../PrivacyScreen";
import { NameStep } from "./NameStep";
import { WelcomeStep } from "./WelcomeStep";

const STEPS = ["welcome", "name"] as const;
type Step = (typeof STEPS)[number];

function savedStep(user: User): Step {
  return user.onboarding_step === "language" || user.onboarding_step === "path" ? "welcome" : "name";
}

/**
 * First run in two screens (TZ 8.1, shortened): language and role, then nickname. The server
 * keeps each answer, so a user who closes the app halfway continues where they stopped.
 */
export function OnboardingFlow() {
  const { t } = useTranslation();
  const { user } = useUser();
  // A moderator reset the nickname of someone who had finished onboarding.
  const nicknameReset = user.onboarded_at != null && user.onboarding_step === "nickname";
  const [step, setStep] = useState<Step>(() => savedStep(user));
  const [document, setDocument] = useState<LegalDocumentKind | null>(null);

  const index = STEPS.indexOf(step);
  const back = useMemo(() => {
    if (document) return () => setDocument(null);
    return index > 0 && !nicknameReset ? () => setStep(STEPS[index - 1]) : undefined;
  }, [document, index, nicknameReset]);
  useTelegramBackButton(back);

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

  if (nicknameReset) {
    return (
      <main className="screen onboarding">
        <NameStep notice={t("onboarding.nicknameReset")} onOpenDocument={setDocument} />
      </main>
    );
  }

  return (
    <main className="screen onboarding">
      <div className="onboarding__progress">
        <div className="dots" role="img" aria-label={t("onboarding.step", { current: index + 1, total: STEPS.length })}>
          {STEPS.map((s, i) => (
            <span key={s} className={i <= index ? "dot is-active" : "dot"} />
          ))}
        </div>
        {index > 0 && !insideTelegram() && (
          <button type="button" className="link-button" onClick={() => setStep(STEPS[index - 1])}>
            ← {t("common.back")}
          </button>
        )}
      </div>
      {step === "welcome" && <WelcomeStep onDone={() => setStep("name")} />}
      {step === "name" && <NameStep onOpenDocument={setDocument} />}
    </main>
  );
}
