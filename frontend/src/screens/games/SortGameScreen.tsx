import { ArrowLeft, ArrowRight } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type CSSProperties, type PointerEvent } from "react";
import { useTranslation } from "react-i18next";
import { useSearchParams } from "react-router";

import { api, type Category, type GameAnswer, type GameRound } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { ProgressBar } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useTr } from "../../i18n/tr";
import { sound } from "../../sound";
import { useCelebrate } from "../../state/celebration";
import { useUser } from "../../state/user";
import { haptic, insideTelegram, useNoVerticalSwipes, useTelegramBackButton } from "../../telegram";
import { RoundResult } from "./RoundResult";
import { SoundToggle } from "./SoundToggle";

/** Seconds per item in the optional quick mode (TZ 8.4). */
const QUICK_SECONDS = 10;
/** A correct answer flies into its bin and the next item comes after this delay. */
const AUTO_NEXT_MS = 650;

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

type Move = { x: number; y: number; flying?: boolean };

/** Dark text on light bin colours, white on dark ones. */
function textOn(hex: string): string {
  const n = Number.parseInt(hex.slice(1), 16);
  const [r, g, b] = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((c) => {
    const v = c / 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.4 ? "#1f2937" : "#ffffff";
}

/** The bin under a point, ignoring the dragged item on top of it. */
function binAt(x: number, y: number): string | null {
  for (const element of document.elementsFromPoint(x, y)) {
    const bin = (element as HTMLElement).closest<HTMLElement>("[data-bin]");
    if (bin?.dataset.bin) return bin.dataset.bin;
  }
  return null;
}

/**
 * Sorting game (TZ 8.4): drag the item into a bin, or tap the bin. All six bins fit on the
 * screen; they show only their name and colour, like real bins, so the picture never gives
 * the answer away. A wrong answer explains itself and shows what that bin takes.
 */
export function SortGameScreen() {
  const { t } = useTranslation();
  const tr = useTr();
  const back = useBack("/games");
  const [params] = useSearchParams();
  const quick = params.get("quick") === "1";
  const { user, setUser } = useUser();
  const celebrate = useCelebrate();
  useNoVerticalSwipes();
  useTelegramBackButton(back);

  const [play, setPlay] = useState<Play | null>(null);
  const [loadError, setLoadError] = useState<unknown>(undefined);
  const [busy, setBusy] = useState(false);
  const [answerError, setAnswerError] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(QUICK_SECONDS);
  const [move, setMove] = useState<Move | null>(null);
  const [over, setOver] = useState<string | null>(null);
  const drag = useRef<{ id: number; x: number; y: number } | null>(null);
  const itemRef = useRef<HTMLDivElement>(null);
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

  /** Send the item flying into a bin (the correct one after an answer). */
  const flyTo = useCallback((bin: string) => {
    const item = itemRef.current?.getBoundingClientRect();
    const target = document.querySelector<HTMLElement>(`[data-bin="${bin}"]`)?.getBoundingClientRect();
    if (!item || !target) return;
    setMove((m) => ({
      x: (m?.x ?? 0) + target.left + target.width / 2 - (item.left + item.width / 2),
      y: (m?.y ?? 0) + target.top + target.height / 3 - (item.top + item.height / 2),
      flying: true,
    }));
  }, []);

  const choose = useCallback(
    async (bin: string | null) => {
      if (!play || play.answer || busy) return;
      const item = play.round.items[play.index];
      setBusy(true);
      setAnswerError(false);
      try {
        const answer = await api.gameAnswer(play.round.round_token, item.id, bin, quick);
        if (answer.correct) {
          haptic.success();
          sound.correct();
          flyTo(answer.correct_bin);
        } else {
          haptic.error();
          sound.wrong();
          setMove(null);
        }
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
        setMove(null);
        setAnswerError(true);
      } finally {
        setBusy(false);
      }
    },
    [play, busy, quick, flyTo, setUser, celebrate],
  );

  const next = useCallback(() => {
    setPlay((p) => (p ? { ...p, index: p.index + 1, answer: null, chosen: null } : p));
    setMove(null);
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

  function onPointerDown(e: PointerEvent<HTMLDivElement>) {
    if (!play || play.answer || busy) return;
    drag.current = { id: e.pointerId, x: e.clientX, y: e.clientY };
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {
      // Some WebViews refuse capture; moves still arrive while the finger stays on the item.
    }
    setMove({ x: 0, y: 0 });
  }

  function onPointerMove(e: PointerEvent<HTMLDivElement>) {
    const start = drag.current;
    if (!start || e.pointerId !== start.id) return;
    setMove({ x: e.clientX - start.x, y: e.clientY - start.y });
    setOver(binAt(e.clientX, e.clientY));
  }

  function onPointerUp(e: PointerEvent<HTMLDivElement>) {
    if (!drag.current || e.pointerId !== drag.current.id) return;
    drag.current = null;
    setOver(null);
    const bin = binAt(e.clientX, e.clientY);
    if (bin) void choose(bin);
    else setMove(null);
  }

  function onPointerCancel() {
    drag.current = null;
    setOver(null);
    setMove(null);
  }

  if (loadError !== undefined || !play) {
    return (
      <main className="screen">
        {!insideTelegram() && (
          <button className="icon-button" type="button" onClick={back} aria-label={t("common.back")}>
            <ArrowLeft size={22} />
          </button>
        )}
        {loadError !== undefined ? <InlineError error={loadError} onRetry={() => void start()} /> : <InlineLoading />}
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
  const correctBin = answer ? play.bins.find((b) => b.code === answer.correct_bin) : undefined;

  function binClass(code: string): string {
    const classes = ["game-bin"];
    if (over === code) classes.push("is-over");
    if (answer) {
      if (code === answer.correct_bin) classes.push("is-correct");
      else if (code === play!.chosen) classes.push("is-wrong");
      else classes.push("is-dimmed");
    }
    return classes.join(" ");
  }

  const itemStyle: CSSProperties | undefined = move
    ? { transform: `translate(${move.x}px, ${move.y}px) scale(${move.flying ? 0.2 : 1.05})`, opacity: move.flying ? 0 : 1 }
    : undefined;
  const itemClass = [
    "game-item",
    move && !move.flying && "is-dragging",
    move?.flying && "is-flying",
    answer && !answer.correct && "is-wrong",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <main className="game-screen">
      <header className="game-top">
        {!insideTelegram() && (
          <button className="icon-button" type="button" onClick={back} aria-label={t("common.back")}>
            <ArrowLeft size={22} />
          </button>
        )}
        <div className="game-top__progress" aria-label={t("sort.round", { current: play.index + 1, total })}>
          <ProgressBar value={play.index + (answer ? 1 : 0)} max={total} />
        </div>
        {play.combo >= 2 && (
          <span className="chip chip--amber chip--sm game-combo">
            <Emoji char="🔥" /> ×{play.combo}
          </span>
        )}
        <span className="chip chip--amber">
          <Emoji char="⭐" /> {play.points}
        </span>
        <SoundToggle />
      </header>

      {quick && !answer && (
        <div className="game-timer" aria-label={t("sort.secondsLeft", { count: secondsLeft })}>
          <ProgressBar value={secondsLeft} max={QUICK_SECONDS} tone="amber" thin />
        </div>
      )}

      <section className={answer && !answer.correct ? "game-stage has-feedback" : "game-stage"} aria-live="polite">
        <div
          ref={itemRef}
          key={item.id}
          className={itemClass}
          style={itemStyle}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerCancel}
        >
          {item.image_url ? <img src={item.image_url} alt="" draggable={false} /> : <Emoji char={item.icon} />}
        </div>
        <h2 className="game-item__name">{tr(item.name)}</h2>

        {!answer && play.index === 0 && <p className="hint small">{t("sort.instruction")}</p>}
        {answer && !answer.correct && (
          <div className="game-feedback card" role="status">
            <strong className="error-text">
              {play.chosen === null ? `${t("sort.timeUp")} ` : ""}
              {t("sort.wrongBin", { bin: tr(correctBin?.name) ?? answer.correct_bin })}
            </strong>
            <p className="text-2">{tr(answer.explanation)}</p>
            {correctBin?.examples && (
              <p className="hint small">
                {t("sort.takes")}: {tr(correctBin.examples)}
              </p>
            )}
            <button type="button" className="btn btn--block" onClick={next}>
              {t("sort.next")} <ArrowRight size={20} />
            </button>
          </div>
        )}
        {answerError && (
          <p className="error-text small" role="alert">
            {t("quiz.answerError")}
          </p>
        )}
      </section>

      {capped && !answer && <p className="hint small game-cap">{t("sort.capReached")}</p>}

      <div className="game-bins">
        {play.bins.map((bin) => (
          <button
            key={bin.code}
            type="button"
            data-bin={bin.code}
            className={binClass(bin.code)}
            style={{ "--bin": bin.color, "--bin-text": textOn(bin.color) } as CSSProperties}
            disabled={busy || Boolean(answer)}
            onClick={() => void choose(bin.code)}
          >
            <span className="game-bin__lid" aria-hidden="true" />
            <span className="game-bin__body">{tr(bin.name)}</span>
          </button>
        ))}
      </div>
    </main>
  );
}
