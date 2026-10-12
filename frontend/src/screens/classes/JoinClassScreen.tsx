import { ShieldCheck } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router";

import { api } from "../../api/client";
import { InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { SubpageHeader } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { haptic } from "../../telegram";
import { classError } from "./parts";

/**
 * Opened from a teacher's QR code: the class and the teacher first, what the teacher will see,
 * then the pupil decides. Joining is always the pupil's own tap.
 */
export function JoinClassScreen() {
  const { code = "" } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const back = useBack("/");
  const preview = useLoad(() => api.previewClass(code), [code]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const info = preview.data;

  async function join() {
    setBusy(true);
    setError(null);
    try {
      await api.joinClass(code);
      haptic.success();
      navigate("/my-class", { replace: true });
    } catch (e) {
      haptic.error();
      setError(classError(t, e));
      setBusy(false);
    }
  }

  return (
    <main className="screen">
      <SubpageHeader onBack={back} />
      {preview.loading && !info && <InlineLoading />}
      {preview.error !== undefined && !info && (
        <section className="screen--center stack join">
          <span className="big-emoji" aria-hidden="true">
            <Emoji char="🔎" />
          </span>
          <p className="text-2">{classError(t, preview.error)}</p>
          <button type="button" className="btn btn--soft" onClick={back}>
            {t("common.back")}
          </button>
        </section>
      )}
      {info && (
        <section className="stack stack--lg join">
          <span className="join__icon" aria-hidden="true">
            <Emoji char="🏫" />
          </span>
          <div className="stack" style={{ gap: 6, textAlign: "center" }}>
            <h1>{info.name}</h1>
            {info.teacher_nickname && <p className="text-2">{t("classes.join.teacher", { name: `@${info.teacher_nickname}` })}</p>}
            <p className="hint small">{t("classes.members", { count: info.member_count })}</p>
          </div>
          {info.is_member ? (
            <button type="button" className="btn btn--block" onClick={() => navigate("/my-class", { replace: true })}>
              {t("classes.join.already")}
            </button>
          ) : (
            <>
              <p className="note row" style={{ alignItems: "flex-start" }}>
                <ShieldCheck size={18} style={{ flex: "none", marginTop: 2 }} aria-hidden="true" />
                {t("classes.join.privacy")}
              </p>
              {error && (
                <p className="error-text" role="alert">
                  {error}
                </p>
              )}
              <button type="button" className="btn btn--block" disabled={busy} onClick={() => void join()}>
                {t("classes.join.button")}
              </button>
              <button type="button" className="link-button" onClick={() => navigate("/", { replace: true })}>
                {t("classes.join.later")}
              </button>
            </>
          )}
        </section>
      )}
    </main>
  );
}
