import { ArrowRight, CircleCheck, CircleX, Lightbulb } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type QuizAnswer, type QuizRound } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { ProgressBar, SubpageHeader } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { useTr } from "../../i18n/tr";
import { useCelebrate } from "../../state/celebration";
import { useUser } from "../../state/user";
import { haptic } from "../../telegram";
import { RoundResult } from "./RoundResult";

const LETTERS = ["A", "B", "C", "D", "E", "F"];

type Play = {
  round: QuizRound;
  index: number;
  answer: QuizAnswer | null;
  chosen: number | null;
  correctCount: number;
  combo: number;
  points: number;
};

export function QuizScreen() {
  const { t } = useTranslation();
  const tr = useTr();
  const back = useBack("/games");
  const { user, setUser } = useUser();
  const celebrate = useCelebrate();
  const overview = useLoad(() => api.games(), []);

  const [topic, setTopic] = useState<string | null>(null);
  const [play, setPlay] = useState<Play | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(false);

  async function start(category: string | null) {
    setTopic(category);
    setBusy(true);
    setError(false);
    try {
      const round = await api.quizRound(category);
      setPlay({ round, index: 0, answer: null, chosen: null, correctCount: 0, combo: 0, points: 0 });
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  async function choose(option: number) {
    if (!play || play.answer || busy) return;
    const question = play.round.questions[play.index];
    setBusy(true);
    setError(false);
    try {
      const answer = await api.quizAnswer(play.round.round_token, question.id, option);
      if (answer.correct) haptic.success();
      else haptic.error();
      setPlay({
        ...play,
        answer,
        chosen: option,
        correctCount: play.correctCount + (answer.correct ? 1 : 0),
        combo: answer.correct ? play.combo + 1 : 0,
        points: play.points + answer.points,
      });
      setUser({ ...user, points_total: answer.points_total });
      celebrate(answer.new_badges ?? []);
    } catch {
      setError(true);
    } finally {
      setBusy(false);
    }
  }

  function next() {
    if (!play) return;
    setPlay({ ...play, index: play.index + 1, answer: null, chosen: null });
  }

  // 1. Topic choice
  if (!play) {
    const games = overview.data;
    return (
      <main className="screen">
        <SubpageHeader onBack={back} title={t("games.quizTitle")} />
        <h1>{t("quiz.chooseTopic")}</h1>
        {overview.loading && !games && <InlineLoading />}
        {overview.error !== undefined && !games && <InlineError error={overview.error} onRetry={overview.reload} />}
        {games && (
          <div className="stack section">
            <button type="button" className="choice" disabled={busy} onClick={() => void start(null)}>
              <span className="choice__icon" aria-hidden="true">
                <Emoji char="🌍" />
              </span>
              <span className="choice__body">
                <span className="choice__title">{t("quiz.mixed")}</span>
                <span className="hint small">{t("games.quizText", { count: games.quiz_total })}</span>
              </span>
            </button>
            {games.quiz_categories.map((c) => (
              <button key={c.code} type="button" className="choice" disabled={busy} onClick={() => void start(c.code)}>
                <span className="choice__icon" aria-hidden="true">
                  <Emoji char={c.icon} />
                </span>
                <span className="choice__body">
                  <span className="choice__title">{tr(c.name)}</span>
                  <span className="hint small">{t("games.quizText", { count: c.question_count })}</span>
                </span>
              </button>
            ))}
          </div>
        )}
        {error && (
          <p className="error-text" role="alert">
            {t("errors.network")}
          </p>
        )}
      </main>
    );
  }

  const total = play.round.questions.length;

  // 3. Result
  if (play.index >= total) {
    return (
      <RoundResult
        game="quiz"
        correct={play.correctCount}
        total={total}
        score={t("quiz.resultScore", { correct: play.correctCount, total })}
        points={play.points}
        onAgain={() => void start(topic)}
        onBack={back}
      />
    );
  }

  // 2. Question
  const question = play.round.questions[play.index];
  const options = tr<string[]>(question.options) ?? [];
  const answer = play.answer;
  const isLast = play.index + 1 === total;

  function optionClass(i: number): string {
    if (!answer) return "answer";
    if (i === answer.correct_index) return "answer is-correct";
    if (i === play!.chosen) return "answer is-wrong";
    return "answer is-dimmed";
  }

  return (
    <main className="screen screen--with-action">
      <SubpageHeader onBack={back} title={t("games.quizTitle")} />
      <div className="round-card">
        <div className="row row--between">
          <span className="row">
            <strong style={{ fontSize: 20 }}>{t("quiz.question", { n: play.index + 1 })}</strong>
            <span className="hint">/ {total}</span>
          </span>
          <span className="row">
            {play.combo >= 2 && (
              <span className="chip chip--amber">
                <Emoji char="🔥" /> {t("quiz.combo", { count: play.combo })}
              </span>
            )}
            <span className="chip chip--neutral">
              {t("quiz.score")}: <strong className="ok-text">{play.points}</strong>
            </span>
          </span>
        </div>
        <ProgressBar value={play.index + (answer ? 1 : 0)} max={total} />
      </div>

      <section className="card question-card section">
        {question.image_url && <img src={question.image_url} alt="" />}
        <h1>{tr(question.text)}</h1>
      </section>

      <div className="answers section">
        {options.map((option, i) => (
          <button
            key={option}
            type="button"
            className={optionClass(i)}
            disabled={busy || Boolean(answer)}
            onClick={() => void choose(i)}
          >
            <span className="answer__letter">{LETTERS[i]}</span>
            <span style={{ flex: 1 }}>{option}</span>
            {answer && i === answer.correct_index && <CircleCheck size={22} className="ok-text" />}
            {answer && i === play.chosen && i !== answer.correct_index && <CircleX size={22} className="error-text" />}
          </button>
        ))}
      </div>

      {answer && (
        <section className={`card feedback section ${answer.correct ? "feedback--ok" : "feedback--bad"}`} role="status">
          <div className="feedback__head">
            <strong className="row">
              <Lightbulb size={20} /> {answer.correct ? t("quiz.correct") : t("quiz.wrong")}
            </strong>
            {answer.points > 0 && <span className="chip chip--sm chip--amber">+{t("quiz.added", { count: answer.points })}</span>}
          </div>
          {answer.correct && answer.points === 0 && <p className="hint small">{t("quiz.alreadyEarned")}</p>}
          <p className="text-2">{tr(answer.explanation)}</p>
        </section>
      )}
      {error && (
        <p className="error-text" role="alert">
          {t("quiz.answerError")}
        </p>
      )}

      {answer && (
        <div className="action-bar">
          <button type="button" className="btn btn--block" onClick={next}>
            {isLast ? t("quiz.finish") : t("quiz.next")} <ArrowRight size={20} />
          </button>
        </div>
      )}
    </main>
  );
}
