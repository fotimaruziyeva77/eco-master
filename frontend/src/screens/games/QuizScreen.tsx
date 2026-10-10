import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type QuizAnswer, type QuizRound } from "../../api/client";
import { InlineError, InlineLoading, SubpageHeader } from "../../components/common";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { useTr } from "../../i18n/tr";
import { useCelebrate } from "../../state/celebration";
import { useUser } from "../../state/user";
import { haptic } from "../../telegram";
import { RoundResult } from "./RoundResult";

type Play = {
  round: QuizRound;
  index: number;
  answer: QuizAnswer | null;
  chosen: number | null;
  correctCount: number;
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
      setPlay({ round, index: 0, answer: null, chosen: null, correctCount: 0, points: 0 });
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
        {overview.loading && !games && <InlineLoading />}
        {overview.error !== undefined && !games && (
          <InlineError error={overview.error} onRetry={overview.reload} />
        )}
        {games && (
          <>
            <h2 className="section-title">{t("quiz.chooseTopic")}</h2>
            <div className="options">
              <button type="button" className="option" disabled={busy} onClick={() => void start(null)}>
                <span className="option__icon" aria-hidden="true">
                  🌍
                </span>
                <span className="option__title">{t("quiz.mixed")}</span>
              </button>
              {games.quiz_categories.map((c) => (
                <button
                  key={c.code}
                  type="button"
                  className="option"
                  disabled={busy}
                  onClick={() => void start(c.code)}
                >
                  <span className="option__icon" aria-hidden="true">
                    {c.icon}
                  </span>
                  <span className="option__title">{tr(c.name)}</span>
                </button>
              ))}
            </div>
          </>
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
        score={t("quiz.resultScore", { correct: play.correctCount, total })}
        points={play.points}
        perfect={play.correctCount === total}
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
      <SubpageHeader onBack={back} />
      <div className="round-head">
        <span className="hint">{t("quiz.questionOf", { current: play.index + 1, total })}</span>
        {play.points > 0 && <span className="badge">+{play.points}</span>}
      </div>
      <div className="progress">
        <div className="progress__bar" style={{ width: `${(play.index / total) * 100}%` }} />
      </div>

      <h1 className="question">{tr(question.text)}</h1>
      {question.image_url && <img className="question__image" src={question.image_url} alt="" />}

      <div className="answers">
        {options.map((option, i) => (
          <button
            key={option}
            type="button"
            className={optionClass(i)}
            disabled={busy || Boolean(answer)}
            onClick={() => void choose(i)}
          >
            {option}
          </button>
        ))}
      </div>

      {answer && (
        <section className={answer.correct ? "feedback feedback--ok" : "feedback feedback--bad"} role="status">
          <strong>
            {answer.correct ? `✓ ${t("quiz.correct")}` : `✗ ${t("quiz.wrong")}`}
            {answer.points > 0 && ` +${t("home.points", { count: answer.points })}`}
          </strong>
          {answer.correct && answer.points === 0 && <p className="hint small">{t("quiz.alreadyEarned")}</p>}
          <p>💡 {tr(answer.explanation)}</p>
        </section>
      )}
      {error && (
        <p className="error-text" role="alert">
          {t("quiz.answerError")}
        </p>
      )}

      {answer && (
        <div className="action-bar">
          <button type="button" className="button button--block" onClick={next}>
            {isLast ? t("quiz.finish") : t("quiz.next")}
          </button>
        </div>
      )}
    </main>
  );
}
