import { useTranslation } from "react-i18next";

import { ShareButton } from "../../components/ShareButton";
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

export function RoundResult({ game, correct, total, score, points, note, onAgain, onBack }: Props) {
  const perfect = correct === total;
  const { t } = useTranslation();
  useTelegramBackButton(onBack);
  return (
    <main className="screen screen--center">
      <div className="intro__art" aria-hidden="true">
        {perfect ? "🏆" : points > 0 ? "🌿" : "🌱"}
      </div>
      <h1>{t("quiz.resultTitle")}</h1>
      <p className="result-score">{score}</p>
      {points > 0 && <span className="chip chip--amber">⭐ +{t("home.points", { count: points })}</span>}
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
