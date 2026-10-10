import { useTranslation } from "react-i18next";

import { useTelegramBackButton } from "../../telegram";

type Props = {
  score: string;
  points: number;
  perfect: boolean;
  note?: string;
  onAgain: () => void;
  onBack: () => void;
};

export function RoundResult({ score, points, perfect, note, onAgain, onBack }: Props) {
  const { t } = useTranslation();
  useTelegramBackButton(onBack);
  return (
    <main className="screen screen--center">
      <div className="emoji emoji--large" aria-hidden="true">
        {perfect ? "🏆" : points > 0 ? "🌿" : "🌱"}
      </div>
      <h1>{t("quiz.resultTitle")}</h1>
      <p className="result-score">{score}</p>
      {points > 0 && <p className="badge">+{t("home.points", { count: points })}</p>}
      {note && <p className="hint small">{note}</p>}
      <button type="button" className="button button--block" onClick={onAgain}>
        {t("quiz.playAgain")}
      </button>
      <button type="button" className="link-button" onClick={onBack}>
        {t("quiz.backToGames")}
      </button>
    </main>
  );
}
