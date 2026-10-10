import {
  CircleQuestionMark,
  Download,
  House,
  ListChecks,
  Send,
  Smartphone,
  Target,
  Waypoints,
} from "lucide-react";
import { useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { api, ApiError, type LessonBody } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { SubpageHeader } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { DEFAULT_LANGUAGE, LANGUAGE_NAMES, LANGUAGES, type Language } from "../../i18n/languages";
import { useUser } from "../../state/user";
import { botChatLink, haptic, insideTelegram, openTelegramLink } from "../../telegram";
import { LESSON_MINUTES } from "./TeachersScreen";

type Status = "busy" | "sent" | "needStart" | "sendError" | "downloadError" | null;

export function LessonScreen() {
  const { slug = "" } = useParams();
  const { t, i18n } = useTranslation();
  const { user } = useUser();
  const back = useBack("/teachers");
  const data = useLoad(() => api.lesson(slug), [slug]);
  // A teacher may use the app in one language and teach in another (TZ 8.9: three languages).
  const [language, setLanguage] = useState<Language>(user.language);
  const [status, setStatus] = useState<Status>(null);

  const lesson = data.data;
  const lang = lesson && language in lesson.body ? language : DEFAULT_LANGUAGE;
  const body = lesson?.body[lang] as LessonBody | undefined;
  const title = lesson ? String(lesson.title[lang] ?? lesson.title[DEFAULT_LANGUAGE]) : "";
  // The lesson and its headings follow the lesson language; buttons follow the app language.
  const lt = i18n.getFixedT(lang);

  async function sendPdf() {
    setStatus("busy");
    try {
      await api.sendLesson(slug, lang);
      haptic.success();
      setStatus("sent");
    } catch (e) {
      haptic.error();
      setStatus(e instanceof ApiError && e.code === "bot_not_started" ? "needStart" : "sendError");
    }
  }

  async function download() {
    setStatus("busy");
    try {
      const url = URL.createObjectURL(await api.lessonPdf(slug, lang));
      const a = document.createElement("a");
      a.href = url;
      a.download = `ekoustoz-${slug}-${lang}.pdf`;
      a.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 10_000);
      setStatus(null);
    } catch {
      setStatus("downloadError");
    }
  }

  const bot = botChatLink();
  return (
    <main className="screen screen--with-action">
      <SubpageHeader onBack={back} title={t("lesson.title")} />
      {data.loading && !lesson && <InlineLoading />}
      {data.error !== undefined && !lesson && <InlineError error={data.error} onRetry={data.reload} />}

      {lesson && body && (
        <article className="stack stack--lg" lang={lang}>
          <div className="stack">
            <div className="chips">
              <span className="chip">{lt("teachers.grade", { grade: lesson.grade })}</span>
              <span className="chip chip--neutral">⏱ {lt("common.minutes", { count: LESSON_MINUTES })}</span>
            </div>
            <h1>{title}</h1>
          </div>

          <div className="stack" style={{ gap: 8 }}>
            <span className="hint small strong" id="lesson-language">
              {t("lesson.language")}
            </span>
            <div className="segmented" role="radiogroup" aria-labelledby="lesson-language">
              {LANGUAGES.map((code) => (
                <button
                  key={code}
                  type="button"
                  role="radio"
                  aria-checked={code === lang}
                  className={code === lang ? "segmented__item is-active" : "segmented__item"}
                  onClick={() => {
                    setLanguage(code);
                    setStatus(null);
                  }}
                >
                  {LANGUAGE_NAMES[code]}
                </button>
              ))}
            </div>
          </div>

          <LessonSection icon={<Target size={20} />} title={lt("lesson.goal")}>
            <p className="text-2">{body.goal}</p>
          </LessonSection>

          <LessonSection icon={<ListChecks size={20} />} title={lt("lesson.materials")}>
            <ul className="lesson-list">
              {body.materials.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </LessonSection>

          <section className="stack">
            <h3 className="row">
              <Waypoints size={20} aria-hidden="true" /> {lt("lesson.plan")}
            </h3>
            {body.plan.map((step) => (
              <div key={step.title} className="card plan-step">
                <span className="plan-step__time">{lt("common.minutes", { count: step.minutes })}</span>
                <h4>{step.title}</h4>
                <p className="text-2">{step.text}</p>
              </div>
            ))}
          </section>

          <LessonSection icon={<CircleQuestionMark size={20} />} title={lt("lesson.questions")}>
            <ol className="lesson-list">
              {body.questions.map((question) => (
                <li key={question}>{question}</li>
              ))}
            </ol>
          </LessonSection>

          <LessonSection icon={<House size={20} />} title={lt("lesson.homework")}>
            <p className="text-2">{body.homework}</p>
          </LessonSection>

          <LessonSection icon={<Smartphone size={20} />} title={lt("lesson.appTask")} soft>
            <p className="text-2">{body.app_task}</p>
          </LessonSection>
        </article>
      )}

      {lesson && (
        <div className="action-bar">
          {status === "sent" && (
            <p className="toast" role="status">
              {t("lesson.sent")}
            </p>
          )}
          {(status === "sendError" || status === "downloadError") && (
            <p className="toast toast--error" role="alert">
              {t(status === "sendError" ? "lesson.sendError" : "lesson.downloadError")}
            </p>
          )}
          {status === "needStart" && (
            <div className="toast toast--error stack" role="alert">
              <span>{t("lesson.needStart")}</span>
              {bot && (
                <button type="button" className="btn btn--sm btn--white" onClick={() => openTelegramLink(bot)}>
                  {t("lesson.openBot")}
                </button>
              )}
            </div>
          )}
          {insideTelegram() ? (
            // Inside Telegram the bot sends the file to the chat: the most reliable way (TZ 8.9).
            <button type="button" className="btn btn--block" disabled={status === "busy"} onClick={() => void sendPdf()}>
              <Send size={20} aria-hidden="true" />
              {status === "busy" ? t("lesson.sending") : t("lesson.sendPdf")}
            </button>
          ) : (
            <button type="button" className="btn btn--block" disabled={status === "busy"} onClick={() => void download()}>
              <Download size={20} aria-hidden="true" /> {t("lesson.download")}
            </button>
          )}
        </div>
      )}
    </main>
  );
}

function LessonSection({
  icon,
  title,
  soft,
  children,
}: {
  icon: ReactNode;
  title: string;
  soft?: boolean;
  children: ReactNode;
}) {
  return (
    <section className={soft ? "card card--soft stack" : "card stack"}>
      <h3 className="row">
        <span className="ok-text row" aria-hidden="true">
          {icon}
        </span>
        {title}
      </h3>
      {children}
    </section>
  );
}
