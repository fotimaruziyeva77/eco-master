import { Check, ChevronRight, Copy, Share2 } from "lucide-react";
import { useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { QrCode } from "../../components/QrCode";
import { SubpageHeader } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { useTr } from "../../i18n/tr";
import { useUser } from "../../state/user";
import { haptic, openTelegramLink, telegramAppLink } from "../../telegram";
import { TeacherClasses } from "../classes/TeacherClasses";

/** Every lesson is one 45-minute class: 5 + 20 + 15 + 5 (TZ 8.9). */
export const LESSON_MINUTES = 45;

export function TeachersScreen() {
  const { t } = useTranslation();
  const tr = useTr();
  const { user } = useUser();
  // Teachers reach this section from home, everyone else from the profile (TZ 8.9).
  const back = useBack(user.path === "teacher" ? "/" : "/profile");
  const lessons = useLoad(() => api.lessons(), []);

  return (
    <main className="screen">
      <SubpageHeader onBack={back} title={t("teachers.title")} />
      <div className="stack stack--lg">
        {user.path === "teacher" && <TeacherClasses />}

        <section className="stack">
          <h2>{t("teachers.lessons")}</h2>
          <p className="hint small">{t("teachers.subtitle")}</p>
          {lessons.loading && !lessons.data && <InlineLoading />}
          {lessons.error !== undefined && !lessons.data && (
            <InlineError error={lessons.error} onRetry={lessons.reload} />
          )}
          {lessons.data?.length === 0 && <p className="hint">{t("teachers.empty")}</p>}
          {lessons.data && lessons.data.length > 0 && (
            <ul className="list">
              {lessons.data.map((lesson, i) => (
                <li key={lesson.slug}>
                  <Link className="list-row" to={`/teachers/${lesson.slug}`}>
                    <span className="icon-tile icon-tile--sky lesson-num" aria-hidden="true">
                      {i + 1}
                    </span>
                    <span className="list-row__text">
                      <strong>{tr(lesson.title)}</strong>
                      <span className="hint small">
                        {t("teachers.grade", { grade: lesson.grade })} ·{" "}
                        {t("common.minutes", { count: LESSON_MINUTES })}
                      </span>
                    </span>
                    <ChevronRight className="list-row__chevron" size={20} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </section>

        <InviteCard />
      </div>
    </main>
  );
}

/** Link and QR code that bring a class into the app (TZ 8.9). */
function InviteCard() {
  const { t } = useTranslation();
  const linkRef = useRef<HTMLElement>(null);
  const [copied, setCopied] = useState(false);
  const [enlarged, setEnlarged] = useState(false);
  const app = telegramAppLink();

  if (!app) {
    return (
      <section className="card stack">
        <h2>{t("teachers.inviteTitle")}</h2>
        <p className="note">{t("teachers.inviteUnavailable")}</p>
      </section>
    );
  }
  // Only a source mark for analytics: no teacher id, no class codes in version 1.
  const link = `${app}?startapp=teacher`;

  async function copy() {
    try {
      await navigator.clipboard.writeText(link);
      haptic.success();
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // No clipboard access: select the link so it can be copied by hand.
      if (linkRef.current) window.getSelection()?.selectAllChildren(linkRef.current);
    }
  }

  function share() {
    const text = t("teachers.inviteShareText");
    openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(link)}&text=${encodeURIComponent(text)}`);
  }

  return (
    <section className="card stack invite">
      <div>
        <h2>{t("teachers.inviteTitle")}</h2>
        <p className="hint small">{t("teachers.inviteText")}</p>
      </div>
      <button type="button" className="qr-button" onClick={() => setEnlarged(true)} aria-label={t("teachers.enlarge")}>
        <QrCode value={link} label={t("teachers.qrLabel")} />
      </button>
      <code ref={linkRef} className="invite__link">
        {link}
      </code>
      <div className="invite__actions">
        <button type="button" className="btn btn--soft" onClick={() => void copy()}>
          {copied ? <Check size={18} aria-hidden="true" /> : <Copy size={18} aria-hidden="true" />}
          {copied ? t("teachers.copied") : t("teachers.copy")}
        </button>
        <button type="button" className="btn btn--soft" onClick={share}>
          <Share2 size={18} aria-hidden="true" /> {t("share.button")}
        </button>
      </div>

      {enlarged && (
        <div
          className="overlay overlay--qr"
          role="dialog"
          aria-modal="true"
          aria-label={t("teachers.qrLabel")}
          onClick={() => setEnlarged(false)}
        >
          <QrCode value={link} label={t("teachers.qrLabel")} className="qr qr--large" />
          <button type="button" className="btn btn--white" autoFocus onClick={() => setEnlarged(false)}>
            {t("common.close")}
          </button>
        </div>
      )}
    </section>
  );
}
