import { CircleCheck, Lock, ShieldCheck } from "lucide-react";
import { useEffect, useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";

import { api, ApiError } from "../../api/client";
import { pickLanguage } from "../../i18n/languages";
import { useUser } from "../../state/user";
import { haptic } from "../../telegram";
import { nicknameFormatError, randomNickname } from "./nickname";

type Check = { state: "idle" | "checking" | "ok" } | { state: "error"; code: string };

export function NicknameStep({ onDone, notice }: { onDone: () => void; notice?: string }) {
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
    <form className="stack stack--lg" onSubmit={(e) => void submit(e)} noValidate>
      <div className="stack">
        <div className="row row--between row--wrap">
          <h1>{t("onboarding.nickname.title")}</h1>
          <span className="chip chip--sm">
            <Lock size={12} /> {t("onboarding.nickname.anonymous")}
          </span>
        </div>
        <p className="hint">{t("onboarding.nickname.subtitle")}</p>
        {notice && (
          <p className="note" role="status">
            {notice}
          </p>
        )}
      </div>

      <div className="card stack">
        <label className="field">
          <span className="field__label">{t("onboarding.nickname.label")}</span>
          <span className={errorCode ? "input-wrap is-invalid" : "input-wrap"}>
            <span className="input-wrap__prefix" aria-hidden="true">
              @
            </span>
            <input
              className="input"
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
            {check.state === "ok" && <CircleCheck size={22} className="ok-text" aria-hidden="true" />}
          </span>
        </label>
        <p id="nickname-status" className="field__status" aria-live="polite">
          {errorCode && <span className="error-text">{t(`onboarding.nicknameErrors.${errorCode || "unknown"}`)}</span>}
          {check.state === "checking" && <span className="hint">{t("onboarding.nickname.checking")}</span>}
          {check.state === "ok" && <span className="ok-text">{t("onboarding.nickname.available")}</span>}
        </p>
        <p className="hint small row" style={{ alignItems: "flex-start" }}>
          <ShieldCheck size={16} style={{ flex: "none", marginTop: 1 }} /> {t("onboarding.nickname.hint")}{" "}
          {t("onboarding.nickname.privacyHint")}
        </p>
        <button
          type="button"
          className="btn btn--soft btn--sm"
          style={{ alignSelf: "flex-start" }}
          onClick={() => setValue(randomNickname(pickLanguage(i18n.language)))}
        >
          {t("onboarding.nickname.suggest")}
        </button>
      </div>

      <button type="submit" className="btn btn--block" disabled={saving || Boolean(errorCode) || !value.trim()}>
        {t("onboarding.nickname.submit")}
      </button>
    </form>
  );
}
