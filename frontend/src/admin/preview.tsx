import { Check, ClipboardList, Lightbulb, ListChecks, MapPin, Play, ShieldAlert, ShieldCheck, Waypoints } from "lucide-react";
import type { ReactNode } from "react";

import { SAFETY_ICON } from "../components/ProjectCard";
import { tint } from "../components/ui";
import i18n from "../i18n";
import type { FieldSpec, Values } from "./api";
import type { Lang, PlanStep } from "./fields";

type Props = { kind: string; values: Values; lang: Lang; fields: FieldSpec[] };

const LETTERS = ["A", "B", "C", "D"];
const CARD_PARTS = [
  ["problem", "⚠️"],
  ["cause", "🔍"],
  ["effect", "🌍"],
  ["solution", "💡"],
] as const;

/** How the item looks in the Mini App, in the chosen language (TZ 8.12 "preview"). */
export function Preview({ kind, values, lang, fields }: Props) {
  const t = i18n.getFixedT(lang);
  const text = (name: string) => ((values[name] as Record<string, string> | null)?.[lang] ?? "").trim();
  const list = (name: string) =>
    ((values[name] as Record<string, string[]> | null)?.[lang] ?? []).filter((v) => v.trim());
  const option = (name: string) =>
    fields.find((f) => f.name === name)?.options?.find((o) => o.value === values[name])?.label ?? "";
  const placeholder = <span className="hint">—</span>;

  if (kind === "project") {
    const safety = (values.safety_level as "green" | "yellow" | "red") ?? "green";
    const difficulty = (values.difficulty as string) ?? "easy";
    return (
      <article className="stack stack--lg">
        <div className="stack">
          <span className="chip" style={{ alignSelf: "flex-start" }}>
            {option("category") || placeholder}
          </span>
          <h1>{text("title") || placeholder}</h1>
          <div className="chips">
            <span className="chip chip--neutral">
              {SAFETY_ICON[safety]} {t(`project.difficulty.${difficulty}`)} — {t(`project.safety.${safety}`)}
            </span>
            <span className="chip chip--neutral">⏱ {t("common.minutes", { count: Number(values.duration_min) || 0 })}</span>
            <span className="chip chip--amber">⭐ +{t("home.points", { count: 15 })}</span>
          </div>
        </div>
        {values.video_url || values.poster_url ? (
          <div
            className="video video--poster"
            style={values.poster_url ? { backgroundImage: `url(${String(values.poster_url)})` } : undefined}
          >
            <span className="video__play" aria-hidden="true">
              <Play size={30} fill="currentColor" />
            </span>
          </div>
        ) : (
          <div className="video video--empty">
            <span className="video__icon" aria-hidden="true">
              🎬
            </span>
            <span className="strong">{t("project.videoSoon")}</span>
          </div>
        )}
        {text("safety_text") && (
          <section className={`safety safety--${safety}`}>
            <span className="icon-tile" aria-hidden="true">
              {safety === "green" ? <ShieldCheck size={22} /> : <ShieldAlert size={22} />}
            </span>
            <div>
              <h3>{t("project.safetyTitle")}</h3>
              <p className="text-2">{text("safety_text")}</p>
            </div>
          </section>
        )}
        <section className="card">
          <h3 className="row">
            <ListChecks size={20} aria-hidden="true" /> {t("project.materials")}
          </h3>
          <ul className="checklist">
            {list("materials").map((item, i) => (
              <li key={i}>
                <button type="button" role="checkbox" aria-checked={false} tabIndex={-1}>
                  <span className="checklist__box" aria-hidden="true">
                    <Check size={14} />
                  </span>
                  <span>{item}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
        <section className="stack">
          <h3 className="row">
            <Waypoints size={20} aria-hidden="true" /> {t("project.steps")}
          </h3>
          {list("steps").map((step, i) => (
            <div key={i} className="card step-card">
              <span className="step-card__num">{i + 1}</span>
              <p>{step}</p>
            </div>
          ))}
        </section>
      </article>
    );
  }

  if (kind === "question") {
    const correct = Number(values.correct_answer) - 1;
    return (
      <div className="stack">
        <span className="chip" style={{ alignSelf: "flex-start" }}>
          {option("category") || "🌍 " + t("quiz.mixed")}
        </span>
        <section className="card question-card">
          {typeof values.image_url === "string" && <img src={values.image_url} alt="" />}
          <h1>{text("text") || placeholder}</h1>
        </section>
        <div className="answers">
          {list("options").map((o, i) => (
            <button key={i} type="button" tabIndex={-1} className={i === correct ? "answer is-correct" : "answer is-dimmed"}>
              <span className="answer__letter">{LETTERS[i]}</span>
              <span style={{ flex: 1 }}>{o}</span>
            </button>
          ))}
        </div>
        <section className="card feedback feedback--ok">
          <div className="feedback__head">
            <strong className="row">
              <Lightbulb size={20} /> {t("quiz.correct")}
            </strong>
          </div>
          <p className="text-2">{text("explanation") || placeholder}</p>
        </section>
      </div>
    );
  }

  if (kind === "game_item") {
    return (
      <div className="stack">
        <p className="hint small">{t("sort.whereDoesItGo")}</p>
        <section className="card" style={{ textAlign: "center" }}>
          <div style={{ fontSize: 64 }} aria-hidden="true">
            {typeof values.image_url === "string" ? (
              <img src={values.image_url} alt="" style={{ width: 96, height: 96, objectFit: "contain" }} />
            ) : (
              (values.icon as string) || "📦"
            )}
          </div>
          <h2>{text("name") || placeholder}</h2>
        </section>
        <span className="chip" style={{ alignSelf: "flex-start" }}>
          ✓ {option("bin") || "—"}
        </span>
        <section className="card feedback feedback--ok">
          <p className="text-2">{text("explanation") || placeholder}</p>
        </section>
      </div>
    );
  }

  if (kind === "daily_task") {
    return (
      <section className="card card--hero">
        <div className="task-card__head">
          <span className="task-card__label">
            <ClipboardList size={15} /> {t("home.taskTitle")}
          </span>
          <span className="task-card__points">⭐ +{t("home.points", { count: Number(values.points) || 0 })}</span>
        </div>
        <p className="task-card__text">{text("text") || "—"}</p>
      </section>
    );
  }

  if (kind === "tip") {
    return (
      <section className="card card--soft tip-card">
        <span className="icon-tile icon-tile--amber" aria-hidden="true">
          <Lightbulb size={22} />
        </span>
        <div>
          <h3>{t("home.tipTitle")}</h3>
          <p className="text-2">{text("text") || placeholder}</p>
        </div>
      </section>
    );
  }

  if (kind === "card") {
    return (
      <article className="stack stack--lg">
        {typeof values.image_url === "string" && <img className="card-picture" src={values.image_url} alt="" />}
        <h1>{text("title") || placeholder}</h1>
        <ol className="chain">
          {CARD_PARTS.filter(([key]) => text(key)).map(([key, icon], i) => (
            <li key={key} className={`card chain__item chain__item--${key}`}>
              <span className="chip chip--sm chip--neutral" style={{ marginBottom: 8 }}>
                {icon} {i + 1}. {t(`card.${key}`)}
              </span>
              <p className="text-2">{text(key)}</p>
            </li>
          ))}
        </ol>
        {text("action") && (
          <section className="card chain__item chain__item--action">
            <h3>🙋 5. {t("card.action")}</h3>
            <p className="text-2">{text("action")}</p>
          </section>
        )}
      </article>
    );
  }

  if (kind === "lesson") {
    const plan = ((values.plan as Record<string, PlanStep[]> | null)?.[lang] ?? []).filter((s) => s.title || s.text);
    const section = (title: string, body: ReactNode) => (
      <section className="card stack">
        <h3>{title}</h3>
        {body}
      </section>
    );
    return (
      <article className="stack stack--lg" lang={lang}>
        <div className="chips">
          <span className="chip">{t("teachers.grade", { grade: values.grade ?? "" })}</span>
          <span className="chip chip--neutral">⏱ {t("common.minutes", { count: 45 })}</span>
        </div>
        <h1>{text("title") || placeholder}</h1>
        {section(t("lesson.goal"), <p className="text-2">{text("goal") || placeholder}</p>)}
        {section(
          t("lesson.materials"),
          <ul className="lesson-list">
            {list("materials").map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>,
        )}
        <section className="stack">
          <h3>{t("lesson.plan")}</h3>
          {plan.map((step, i) => (
            <div key={i} className="card plan-step">
              <span className="plan-step__time">{t("common.minutes", { count: step.minutes ?? 0 })}</span>
              <h4>{step.title}</h4>
              <p className="text-2">{step.text}</p>
            </div>
          ))}
        </section>
        {section(
          t("lesson.questions"),
          <ol className="lesson-list">
            {list("questions").map((q, i) => (
              <li key={i}>{q}</li>
            ))}
          </ol>,
        )}
        {section(t("lesson.homework"), <p className="text-2">{text("homework") || placeholder}</p>)}
        {section(t("lesson.appTask"), <p className="text-2">{text("app_task") || placeholder}</p>)}
      </article>
    );
  }

  if (kind === "pickup_point") {
    // As the market shows it under a listing that is given away.
    return (
      <section className="card point-card" lang={lang}>
        <span className="icon-tile icon-tile--sky" aria-hidden="true">
          <MapPin size={22} />
        </span>
        <div className="stack" style={{ gap: 4 }}>
          <span className="hint small">{t("market.point")}</span>
          <strong>{text("name") || placeholder}</strong>
          <span className="text-2">{text("address") || placeholder}</span>
          <span className="hint small">{t("market.hours", { hours: text("hours") || "—" })}</span>
        </div>
      </section>
    );
  }

  // Waste type: the chip on the home screen and the bin in the sorting game.
  return (
    <div className="stack">
      <span className="category-chip" style={tint((values.color as string) || "#10B981")}>
        <span className="category-chip__icon" aria-hidden="true">
          {(values.icon as string) || "♻️"}
        </span>
        <span>
          <strong>{text("name") || "—"}</strong>
          <small>{text("examples")}</small>
        </span>
      </span>
    </div>
  );
}
