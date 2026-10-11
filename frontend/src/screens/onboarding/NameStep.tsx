import { CircleCheck, Dices } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { Trans, useTranslation } from "react-i18next";

import { api, ApiError } from "../../api/client";
import { Emoji } from "../../components/Emoji";
import { Toggle } from "../../components/ui";
import { pickLanguage } from "../../i18n/languages";
import { useUser } from "../../state/user";
import { haptic, requestWriteAccess } from "../../telegram";
import type { LegalDocumentKind } from "../PrivacyScreen";
import { nicknameFormatError, randomNickname } from "./nickname";

type Check = { state: "idle" | "checking" | "ok" } | { state: "error"; code: string };

/**
 * Second and last screen: a nickname (a ready one to keep or change), daily reminders and the
 * consent line, then the app. After a moderator reset only the nickname is asked again.
 */
export function NameStep({
  notice,
  onOpenDocument,
}: {
  /** Set when a moderator asked for a new nickname: no reminders or consent again. */
  notice?: string;
  onOpenDocument: (kind: LegalDocumentKind) => void;
}) {
  const { t, i18n } = useTranslation();
  const { user, setUser } = useUser();
  const [value, setValue] = useState(() => user.nickname ?? randomNickname(pickLanguage(i18n.language)));
  const [check, setCheck] = useState<Check>({ state: "idle" });
  const [reminders, setReminders] = useState(true);
  const [saving, setSaving] = useState(false);

  // Validate the format at once and ask the server (taken / forbidden) after a pause in typing.
  useEffect(() => {
    if (!value.trim()) {
      setCheck({ state: "idle" });
      return;
    }
    const formatError = nicknameFormatError(value);
    if (formatError) {
      setCheck({ state: "error", code: formatError });
      return;
    }
    setCheck({ state: "checking" });
    let alive = true;
    const timer = window.setTimeout(() => {
      api.checkNickname(value.trim()).then(
        (r) => alive && setCheck(r.ok ? { state: "ok" } : { state: "error", code: r.error ?? "" }),
        () => alive && setCheck({ state: "idle" }),
      );
    }, 400);
    return () => {
      alive = false;
      window.clearTimeout(timer);
    };
  }, [value]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    const formatError = nicknameFormatError(value);
    if (formatError) {
      setCheck({ state: "error", code: formatError });
      haptic.error();
      return;
    }
    setSaving(true);
    try {
      setUser(await api.onboardingNickname(value.trim()));
      if (!notice) {
        // Reminders need the user's permission for the bot to write (TZ 8.1). Declining is fine.
        if (reminders && !user.write_access && (await requestWriteAccess())) {
          await api.setWriteAccess(true);
        }
        await api.updateMe({ reminders_enabled: reminders });
      }
      const done = await api.onboardingComplete();
      haptic.success();
      setUser(done);
    } catch (error) {
      haptic.error();
      setCheck({
        state: "error",
        code: error instanceof ApiError && error.code.startsWith("nickname_") ? error.code : "unknown",
      });
      setSaving(false);
    }
  }

  const errorCode = check.state === "error" ? check.code : null;

  return (
    <form className="stack stack--lg" onSubmit={(e) => void submit(e)} noValidate>
      <div className="stack">
        <h1>{t("onboarding.nickname.title")}</h1>
        <p className="hint">{notice ?? t("onboarding.nickname.subtitle")}</p>
      </div>

      <div className="stack" style={{ gap: 8 }}>
        <div className="row">
          <span className={errorCode ? "input-wrap is-invalid" : "input-wrap"} style={{ flex: 1 }}>
            <span className="input-wrap__prefix" aria-hidden="true">
              @
            </span>
            <input
              className="input"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              maxLength={32}
              autoComplete="off"
              autoCapitalize="off"
              spellCheck={false}
              aria-label={t("onboarding.nickname.label")}
              aria-invalid={Boolean(errorCode)}
              aria-describedby="nickname-status"
            />
            {check.state === "ok" && <CircleCheck size={22} className="ok-text" aria-hidden="true" />}
          </span>
          <button
            type="button"
            className="icon-button"
            aria-label={t("onboarding.nickname.suggest")}
            onClick={() => {
              haptic.tap();
              setValue(randomNickname(pickLanguage(i18n.language)));
            }}
          >
            <Dices size={22} />
          </button>
        </div>
        <p id="nickname-status" className="field__status small" aria-live="polite">
          {errorCode && <span className="error-text">{t(`onboarding.nicknameErrors.${errorCode || "unknown"}`)}</span>}
          {check.state === "checking" && <span className="hint">{t("onboarding.nickname.checking")}</span>}
        </p>
      </div>

      {!notice && (
        <div className="card card--soft row" style={{ gap: 12 }}>
          <Emoji char="🔔" className="welcome__bell" />
          <span className="list-row__text">
            <strong>{t("onboarding.intro.remindersTitle")}</strong>
          </span>
          <Toggle checked={reminders} onChange={setReminders} label={t("onboarding.intro.remindersTitle")} />
        </div>
      )}

      <button type="submit" className="btn btn--block" disabled={saving || Boolean(errorCode) || !value.trim()}>
        {t("onboarding.intro.start")} <Emoji char="🌱" />
      </button>

      {!notice && (
        <p className="hint small consent">
          <Trans
            i18nKey="onboarding.intro.consent"
            components={{
              policy: <button type="button" className="link-inline" onClick={() => onOpenDocument("privacy")} />,
              terms: <button type="button" className="link-inline" onClick={() => onOpenDocument("terms")} />,
            }}
          />
        </p>
      )}
    </form>
  );
}
