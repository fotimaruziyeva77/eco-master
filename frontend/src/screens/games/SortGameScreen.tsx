import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { api, type Category, type GameAnswer, type GameRound } from "../../api/client";
import { InlineError, InlineLoading, SubpageHeader } from "../../components/common";
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
  points: number;
  capped: boolean;
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
        points: 0,
        capped: overview.game_points_today >= overview.game_daily_cap,
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
        const answer = await api.gameAnswer(play.round.round_token, item.id, bin);
        if (answer.correct) haptic.success();
        else haptic.error();
        setPlay({
          ...play,
          answer,
          chosen: bin,
          correctCount: play.correctCount + (answer.correct ? 1 : 0),
          points: play.points + answer.points,
          capped: answer.points_today >= answer.daily_cap,
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
  if (play.index >= total) {
    return (
      <RoundResult
        score={t("sort.resultScore", { correct: play.correctCount, total })}
        points={play.points}
        perfect={play.correctCount === total}
        note={play.capped ? t("sort.capReached") : undefined}
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
      <SubpageHeader onBack={back} />
      <div className="round-head">
        <span className="hint">{t("sort.itemOf", { current: play.index + 1, total })}</span>
        {play.points > 0 && <span className="badge">+{play.points}</span>}
      </div>
      {quick && !answer && (
        <div className="progress progress--timer" aria-label={t("sort.secondsLeft", { count: secondsLeft })}>
          <div className="progress__bar" style={{ width: `${(secondsLeft / QUICK_SECONDS) * 100}%` }} />
        </div>
      )}

      <section className="sort-item" aria-live="polite">
        <div className="sort-item__visual" aria-hidden="true">
          {item.image_url ? <img src={item.image_url} alt="" /> : item.icon}
        </div>
        <h1>{tr(item.name)}</h1>
        {!answer && <p className="hint">{t("sort.whereDoesItGo")}</p>}
      </section>

      <div className="bins">
        {play.bins.map((bin) => (
          <button
            key={bin.code}
            type="button"
            className={binClass(bin.code)}
            style={answer ? undefined : { borderColor: bin.color }}
            disabled={busy || Boolean(answer)}
            onClick={() => void choose(bin.code)}
          >
            <span className="bin__icon" aria-hidden="true">
              {bin.icon}
            </span>
            <span>{tr(bin.name)}</span>
          </button>
        ))}
      </div>

      {answer && (
        <section className={answer.correct ? "feedback feedback--ok" : "feedback feedback--bad"} role="status">
          <strong>
            {answer.correct
              ? `✓ ${t("sort.correct")}${answer.points ? ` +${answer.points}` : ""}`
              : play.chosen === null
                ? `⏰ ${t("sort.timeUp")} ${t("sort.wrongBin", { bin: binName(answer.correct_bin) })}`
                : `✗ ${t("sort.wrongBin", { bin: binName(answer.correct_bin) })}`}
          </strong>
          {!answer.correct && <p>💡 {tr(answer.explanation)}</p>}
          {!answer.correct && (
            <button type="button" className="button button--block" onClick={next}>
              {t("sort.next")}
            </button>
          )}
        </section>
      )}
      {play.capped && !answer && <p className="hint small">{t("sort.capReached")}</p>}
      {answerError && (
        <p className="error-text" role="alert">
          {t("quiz.answerError")}
        </p>
      )}
    </main>
  );
}
