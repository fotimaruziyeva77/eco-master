import { Check, ChevronRight, Clock, Link2, Play } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { Emoji } from "../components/Emoji";
import { SubpageHeader } from "../components/ui";
import { useBack } from "../hooks/useBack";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";
import { haptic } from "../telegram";

// Fixed order (TZ 8.10); the server's JSON does not preserve key order.
const CHAIN = [
  { key: "problem", icon: "⚠️" },
  { key: "cause", icon: "🔍" },
  { key: "effect", icon: "🌡️" },
  { key: "solution", icon: "🌱" },
] as const;

/** Reading speed for the "N min read" label. */
const WORDS_PER_MINUTE = 150;

function splitSentences(text: string): string[] {
  // No regex look-behind: older iOS WebViews (before 16.4) fail to parse it.
  return (text.match(/[^.!?]+[.!?]+|[^.!?]+$/g) ?? [])
    .map((s) => s.trim())
    .filter(Boolean);
}

export function CardScreen() {
  const { slug = "" } = useParams();
  const { t } = useTranslation();
  const tr = useTr();
  const back = useBack("/learn");
  const data = useLoad(() => Promise.all([api.card(slug), api.cards()]), [slug]);
  const [done, setDone] = useState<Set<number>>(new Set());

  const [card, all] = data.data ?? [undefined, []];
  const sections = tr<Record<string, string>>(card?.sections);
  const actions = sections?.action ? splitSentences(sections.action) : [];
  const words = sections ? Object.values(sections).join(" ").split(/\s+/).length : 0;
  const index = all.findIndex((c) => c.slug === slug);

  function toggle(i: number) {
    haptic.tap();
    setDone((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  return (
    <main className="screen">
      <SubpageHeader onBack={back} title={t("learn.cards")} />
      {all.length > 1 && (
        <nav className="chip-scroll card-tabs" aria-label={t("learn.cards")}>
          {all.map((c) => (
            <Link key={c.slug} to={`/cards/${c.slug}`} replace className={c.slug === slug ? "is-active" : undefined}>
              {tr(c.title)}
            </Link>
          ))}
        </nav>
      )}
      {data.loading && !data.data && <InlineLoading />}
      {data.error !== undefined && !data.data && <InlineError error={data.error} onRetry={data.reload} />}

      {card && sections && (
        <article className="stack stack--lg">
          <div className="row row--wrap">
            <span className="chip chip--sm">
              {t("card.position", { current: index + 1, total: all.length })}
            </span>
            <span className="chip chip--sm chip--neutral">
              <Clock size={12} /> {t("card.readTime", { count: Math.max(1, Math.round(words / WORDS_PER_MINUTE)) })}
            </span>
          </div>
          <h1>{tr(card.title)}</h1>

          <section className="stack">
            <h2 className="row">
              <Link2 size={20} aria-hidden="true" /> {t("card.chain")}
            </h2>
            <ol className="chain">
              {CHAIN.filter(({ key }) => sections[key]).map(({ key, icon }, i) => (
                <li key={key} className={`card chain__item chain__item--${key}`}>
                  <span className="chip chip--sm chip--neutral" style={{ marginBottom: 8 }}>
                    <Emoji char={icon} /> {i + 1}. {t(`card.${key}`)}
                  </span>
                  <p className="text-2">{sections[key]}</p>
                </li>
              ))}
            </ol>
          </section>

          {actions.length > 0 && (
            <section className="card chain__item chain__item--action">
              <h3>
                <Emoji char="🙋" /> 5. {t("card.action")}
              </h3>
              <ul className="checklist">
                {actions.map((action, i) => (
                  <li key={action}>
                    <button type="button" role="checkbox" aria-checked={done.has(i)} onClick={() => toggle(i)}>
                      <span className="checklist__box" aria-hidden="true">
                        <Check size={14} />
                      </span>
                      <span>{action}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          )}

          <Link className="card card--amber row" to="/games/quiz" style={{ textDecoration: "none", gap: 12 }}>
            <span className="flame" aria-hidden="true">
              <Play size={20} />
            </span>
            <span className="list-row__text">
              <strong>{t("card.quizTitle")}</strong>
              <span className="small text-2">{t("card.quizText")}</span>
            </span>
            <ChevronRight size={20} />
          </Link>
        </article>
      )}
    </main>
  );
}
