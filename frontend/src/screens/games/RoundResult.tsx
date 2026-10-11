import { useEffect } from "react";
import { useTranslation } from "react-i18next";

import { Confetti } from "../../components/Confetti";
import { Emoji } from "../../components/Emoji";
import { ShareButton } from "../../components/ShareButton";
import { sound } from "../../sound";
import { useTelegramBackButton } from "../../telegram";

type Props = {
  game: "quiz" | "sort";
  correct: number;
  total: number;
  score: string;
  points: number;
  note?: string;
  onAgain: () => void;
  onBack: () => void;
};

/** End of a round: stars for the share of right answers, confetti for a perfect one. */
export function RoundResult({ game, correct, total, score, points, note, onAgain, onBack }: Props) {
  const perfect = correct === total;
  const stars = correct === 0 ? 0 : perfect ? 3 : correct * 2 >= total ? 2 : 1;
  const { t } = useTranslation();
  useTelegramBackButton(onBack);
  useEffect(() => {
    if (stars >= 2) sound.fanfare();
  }, [stars]);

  return (
    <main className="screen screen--center">
      {perfect && <Confetti />}
      <div className="result-stars" role="img" aria-label={score}>
        {[1, 2, 3].map((n) => (
          <span key={n} className={n <= stars ? "is-on" : undefined}>
            <Emoji char="⭐" />
          </span>
        ))}
      </div>
      <h1>{t(perfect ? "quiz.perfect" : stars >= 2 ? "quiz.great" : "quiz.resultTitle")}</h1>
      <p className="result-score">{score}</p>
      {points > 0 && (
        <span className="chip chip--amber">
          <Emoji char="⭐" /> +{t("home.points", { count: points })}
        </span>
      )}
      {note && <p className="hint small">{note}</p>}
      <div className="stack" style={{ width: "100%", marginTop: 16 }}>
        <button type="button" className="btn btn--block" onClick={onAgain}>
          {t("quiz.playAgain")}
        </button>
        {correct > 0 && <ShareButton kind={game} objectId={`${correct}/${total}`} label={t("share.result")} />}
        <button type="button" className="link-button" onClick={onBack}>
          {t("quiz.backToGames")}
        </button>
      </div>
    </main>
  );
}
