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
        <button type="button" className="btn btn--soft btn--block" onClick={onBack}>
          {t("quiz.backToGames")}
        </button>
      </div>
    </main>
  );
}
