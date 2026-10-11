import { Hand, HelpCircle, Lightbulb } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { api, type Category, type GameAnswer, type GameRound } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { ProgressBar, SubpageHeader, tint } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useTr } from "../../i18n/tr";
import { useCelebrate } from "../../state/celebration";
import { useUser } from "../../state/user";
import { haptic, useNoVerticalSwipes } from "../../telegram";
import { RoundResult } from "./RoundResult";

/** Seconds per item in the optional quick mode (TZ 8.4). */
const QUICK_SECONDS = 10;
/** A correct answer moves on by itself after this delay; a wrong one waits for "Next". */
const AUTO_NEXT_MS = 900;

type Play = {
  round: GameRound;
  bins: Category[];
  index: number;
  answer: GameAnswer | null;
  chosen: string | null;
  correctCount: number;
  combo: number;
  points: number;
  pointsToday: number;
  dailyCap: number;
};

export function SortGameScreen() {
  const { t } = useTranslation();
  const tr = useTr();
  const back = useBack("/games");
  const [params] = useSearchParams();
  const quick = params.get("quick") === "1";
  const { user, setUser } = useUser();
  const celebrate = useCelebrate();
  useNoVerticalSwipes();

  const [play, setPlay] = useState<Play | null>(null);
  const [loadError, setLoadError] = useState<unknown>(undefined);
  const [busy, setBusy] = useState(false);
  const [answerError, setAnswerError] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(QUICK_SECONDS);
  const userRef = useRef(user);
  userRef.current = user;

  const start = useCallback(async () => {
    setLoadError(undefined);
    setPlay(null);
    try {
      const [round, overview] = await Promise.all([api.gameRound(), api.games()]);
      setPlay({
        round,
        bins: overview.bins,
        index: 0,
        answer: null,
        chosen: null,
        correctCount: 0,
        combo: 0,
        points: 0,
        pointsToday: overview.game_points_today,
        dailyCap: overview.game_daily_cap,
      });
      setSecondsLeft(QUICK_SECONDS);
    } catch (error) {
      setLoadError(error);
    }
  }, []);

  useEffect(() => {
    void start();
  }, [start]);

  const choose = useCallback(
    async (bin: string | null) => {
      if (!play || play.answer || busy) return;
      const item = play.round.items[play.index];
      setBusy(true);
      setAnswerError(false);
      try {
        const answer = await api.gameAnswer(play.round.round_token, item.id, bin, quick);
        if (answer.correct) haptic.success();
        else haptic.error();
        setPlay({
          ...play,
          answer,
          chosen: bin,
          correctCount: play.correctCount + (answer.correct ? 1 : 0),
          combo: answer.correct ? play.combo + 1 : 0,
          points: play.points + answer.points,
          pointsToday: answer.points_today,
          dailyCap: answer.daily_cap,
        });
        setUser({ ...userRef.current, points_total: answer.points_total });
        celebrate(answer.new_badges ?? []);
      } catch {
        setAnswerError(true);
      } finally {
        setBusy(false);
      }
    },
    [play, busy, setUser, celebrate],
  );

  const next = useCallback(() => {
    setPlay((p) => (p ? { ...p, index: p.index + 1, answer: null, chosen: null } : p));
    setSecondsLeft(QUICK_SECONDS);
  }, []);

  // Quick mode: count down while the item is unanswered; time out as a wrong answer.
  const waiting = Boolean(play && !play.answer && play.index < play.round.items.length);
  useEffect(() => {
    if (!quick || !waiting || busy) return;
    if (secondsLeft <= 0) {
      void choose(null);
      return;
    }
    const timer = window.setTimeout(() => setSecondsLeft((s) => s - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [quick, waiting, busy, secondsLeft, choose]);

  // A correct answer moves on by itself.
  useEffect(() => {
    if (!play?.answer?.correct) return;
    const timer = window.setTimeout(next, AUTO_NEXT_MS);
    return () => window.clearTimeout(timer);
  }, [play?.answer, next]);

  if (loadError !== undefined) {
    return (
      <main className="screen">
        <SubpageHeader onBack={back} />
        <InlineError error={loadError} onRetry={() => void start()} />
      </main>
    );
  }
  if (!play) {
    return (
      <main className="screen">
        <SubpageHeader onBack={back} />
        <InlineLoading />
      </main>
    );
  }

  const total = play.round.items.length;
  const capped = play.pointsToday >= play.dailyCap;
  if (play.index >= total) {
    return (
      <RoundResult
        game="sort"
        correct={play.correctCount}
        total={total}
        score={t("sort.resultScore", { correct: play.correctCount, total })}
        points={play.points}
        note={capped ? t("sort.capReached") : undefined}
        onAgain={() => void start()}
        onBack={back}
      />
    );
  }

  const item = play.round.items[play.index];
  const answer = play.answer;
  const binName = (code: string) => tr(play.bins.find((b) => b.code === code)?.name) ?? code;

  function binClass(code: string): string {
    if (!answer) return "bin";
    if (code === answer.correct_bin) return "bin is-correct";
    if (code === play!.chosen) return "bin is-wrong";
    return "bin is-dimmed";
  }

  return (
    <main className="screen sort-game">
      <SubpageHeader onBack={back} title={t("games.sortTitle")} />

      <section className="card round-card">
        <div className="row row--between row--wrap">
          <span className="row">
            <span className="chip chip--neutral">{t("sort.round", { current: play.index + 1, total })}</span>
            {play.combo >= 2 && (
              <span className="chip chip--amber">
                <Emoji char="🔥" /> {t("quiz.combo", { count: play.combo })}
              </span>
            )}
          </span>
          {play.points > 0 && (
            <span className="chip chip--amber">
              <Emoji char="⭐" /> +{play.points}
            </span>
          )}
        </div>
        <div className="row row--between small strong">
          <span>{t("games.dailyLimit", { points: play.pointsToday, cap: play.dailyCap })}</span>
        </div>
        {quick && !answer ? (
          <div aria-label={t("sort.secondsLeft", { count: secondsLeft })}>
            <ProgressBar value={secondsLeft} max={QUICK_SECONDS} tone="amber" />
          </div>
        ) : (
          <ProgressBar value={play.pointsToday} max={play.dailyCap} />
        )}
      </section>

      <p className="note row section" style={{ background: "var(--primary-soft)", color: "var(--on-primary-soft)" }}>
        <Hand size={18} aria-hidden="true" /> {t("sort.instruction")}
      </p>

      <section className="card sort-item section" aria-live="polite">
        <span className="chip">
          <HelpCircle size={14} /> {t("sort.whereDoesItGo")}
        </span>
        <div className="sort-item__visual" aria-hidden="true">
          {item.image_url ? <img src={item.image_url} alt="" /> : <Emoji char={item.icon} />}
        </div>
        <h2>{tr(item.name)}</h2>
      </section>

      <div className="section-head section">
        <h3>{t("sort.bins")}</h3>
      </div>
      <div className="bins">
        {play.bins.map((bin) => (
          <button
            key={bin.code}
            type="button"
            className={binClass(bin.code)}
            disabled={busy || Boolean(answer)}
            onClick={() => void choose(bin.code)}
          >
            <span className="bin__icon" style={tint(bin.color, "33")} aria-hidden="true">
              <Emoji char={bin.icon} />
            </span>
            <span className="bin__text">
              <strong>{tr(bin.name)}</strong>
              {bin.examples && <small>{tr(bin.examples)}</small>}
            </span>
          </button>
        ))}
      </div>

      {answer && (
        <section className={`card feedback section ${answer.correct ? "feedback--ok" : "feedback--bad"}`} role="status">
          <div className="feedback__head">
            <strong>
              {answer.correct
                ? `✓ ${t("sort.correct")}`
                : play.chosen === null
                  ? `⏰ ${t("sort.timeUp")}`
                  : `✗ ${t("sort.wrongBin", { bin: binName(answer.correct_bin) })}`}
            </strong>
            {answer.points > 0 && <span className="chip chip--sm chip--amber">+{answer.points}</span>}
          </div>
          {!answer.correct && (
            <>
              {play.chosen === null && <p className="strong">{t("sort.wrongBin", { bin: binName(answer.correct_bin) })}</p>}
              <p className="text-2 row" style={{ alignItems: "flex-start" }}>
                <Lightbulb size={18} style={{ flex: "none", marginTop: 2 }} /> {tr(answer.explanation)}
              </p>
              <button type="button" className="btn btn--block" style={{ marginTop: 12 }} onClick={next}>
                {t("sort.next")}
              </button>
            </>
          )}
        </section>
      )}
      {capped && !answer && <p className="hint small section">{t("sort.capReached")}</p>}
      {answerError && (
        <p className="error-text" role="alert">
          {t("quiz.answerError")}
        </p>
      )}
    </main>
  );
}
