import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { api, ApiError } from "../../api/client";
import { pickLanguage } from "../../i18n/languages";
import { useUser } from "../../state/user";
import { haptic } from "../../telegram";
import { nicknameFormatError, randomNickname } from "./nickname";

type Check = { state: "idle" | "checking" | "ok" } | { state: "error"; code: string };

export function NicknameStep({ onDone }: { onDone: () => void }) {
  const { t, i18n } = useTranslation();
  const { user, setUser } = useUser();
  const [value, setValue] = useState(user.nickname ?? "");
  const [check, setCheck] = useState<Check>({ state: "idle" });
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
      haptic.success();
      onDone();
    } catch (error) {
      haptic.error();
      setCheck({
        state: "error",
        code: error instanceof ApiError && error.code.startsWith("nickname_") ? error.code : "unknown",
      });
    } finally {
      setSaving(false);
    }
  }

  const errorCode = check.state === "error" ? check.code : null;

  return (
    <form onSubmit={(e) => void submit(e)} noValidate>
      <h1>{t("onboarding.nickname.title")}</h1>
      <p className="hint">{t("onboarding.nickname.subtitle")}</p>

      <label className="field">
        <span className="field__label">{t("onboarding.nickname.label")}</span>
        <input
          className={errorCode ? "input is-invalid" : "input"}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder={t("onboarding.nickname.placeholder")}
          maxLength={32}
          autoComplete="off"
          autoCapitalize="off"
          spellCheck={false}
          aria-invalid={Boolean(errorCode)}
          aria-describedby="nickname-status"
        />
      </label>

      <p id="nickname-status" className="field__status" aria-live="polite">
        {errorCode && (
          <span className="error-text">{t(`onboarding.nicknameErrors.${errorCode || "unknown"}`)}</span>
        )}
        {check.state === "checking" && <span className="hint">{t("onboarding.nickname.checking")}</span>}
        {check.state === "ok" && <span className="ok-text">{t("onboarding.nickname.available")}</span>}
        {check.state === "idle" && <span className="hint">{t("onboarding.nickname.hint")}</span>}
      </p>
      <p className="hint small">🔒 {t("onboarding.nickname.privacyHint")}</p>

      <button
        type="button"
        className="button button--secondary"
        onClick={() => setValue(randomNickname(pickLanguage(i18n.language)))}
      >
        {t("onboarding.nickname.suggest")}
      </button>
      <button
        type="submit"
        className="button button--block"
        disabled={saving || Boolean(errorCode) || !value.trim()}
      >
        {t("onboarding.nickname.submit")}
      </button>
    </form>
  );
}
