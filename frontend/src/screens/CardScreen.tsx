import { ArrowLeft, ArrowRight, Check } from "lucide-react";
import { useRef, useState, type TouchEvent } from "react";
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
const PARTS = [
  { key: "problem", icon: "⚠️" },
  { key: "cause", icon: "🔍" },
  { key: "effect", icon: "🌡️" },
  { key: "solution", icon: "🌱" },
  { key: "action", icon: "🙋" },
] as const;

/** A swipe of at least this many pixels turns the page. */
const SWIPE = 50;

function splitSentences(text: string): string[] {
  // No regex look-behind: older iOS WebViews (before 16.4) fail to parse it.
  return (text.match(/[^.!?]+[.!?]+|[^.!?]+$/g) ?? [])
    .map((s) => s.trim())
    .filter(Boolean);
}

/**
 * Knowledge card as a story (TZ 8.10): one part of the chain per page — problem, cause,
 * effect, solution, what I can do — with a big picture, read by tapping or swiping.
 */
export function CardScreen() {
  const { slug = "" } = useParams();
  const { t } = useTranslation();
  const tr = useTr();
  const back = useBack("/learn");
  const data = useLoad(() => api.card(slug), [slug]);
  const [page, setPage] = useState(0);
  const [done, setDone] = useState<Set<number>>(new Set());
  const touch = useRef<number | null>(null);

  const card = data.data;
  const sections = tr<Record<string, string>>(card?.sections);
  const parts = PARTS.filter(({ key }) => sections?.[key]);
  const last = parts.length - 1;
  const part = parts[Math.min(page, last)];
  const actions = part?.key === "action" && sections ? splitSentences(sections.action) : [];

  function go(next: number) {
    if (next < 0 || next > last) return;
    haptic.tap();
    setPage(next);
  }

  function toggle(i: number) {
    haptic.tap();
    setDone((prev) => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  function onTouchEnd(e: TouchEvent) {
    const start = touch.current;
    touch.current = null;
    if (start === null) return;
    const dx = e.changedTouches[0].clientX - start;
    if (dx <= -SWIPE) go(page + 1);
    else if (dx >= SWIPE) go(page - 1);
  }

  return (
    <main className="screen screen--with-action">
      <SubpageHeader onBack={back} title={card ? tr(card.title) : t("learn.cards")} />
      {data.loading && !card && <InlineLoading />}
      {data.error !== undefined && !card && <InlineError error={data.error} onRetry={data.reload} />}

      {card && part && (
        <>
          <div className="story-bar" aria-hidden="true">
            {parts.map(({ key }, i) => (
              <span key={key} className={i <= page ? "is-on" : undefined} />
            ))}
          </div>
          <article
            key={part.key}
            className={`story story--${part.key}`}
            onTouchStart={(e) => (touch.current = e.touches[0].clientX)}
            onTouchEnd={onTouchEnd}
          >
            {page === 0 && card.image_url ? (
              <img className="card-picture" src={card.image_url} alt="" />
            ) : (
              <span className="story__icon" aria-hidden="true">
                <Emoji char={part.icon} />
              </span>
            )}
            <span className="chip story__label">{t(`card.${part.key}`)}</span>
            {part.key === "action" ? (
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
            ) : (
              <p className="story__text">{sections?.[part.key]}</p>
            )}
          </article>
        </>
      )}

      {card && part && (
        <div className="action-bar">
          <div className="row">
            {page > 0 && (
              <button type="button" className="btn btn--soft story__prev" onClick={() => go(page - 1)} aria-label={t("common.back")}>
                <ArrowLeft size={20} />
              </button>
            )}
            {page < last ? (
              <button type="button" className="btn btn--block" onClick={() => go(page + 1)}>
                {t("card.next")} <ArrowRight size={20} />
              </button>
            ) : (
              <Link className="btn btn--block" to="/games/quiz">
                <Emoji char="🧠" /> {t("card.quizTitle")}
              </Link>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
