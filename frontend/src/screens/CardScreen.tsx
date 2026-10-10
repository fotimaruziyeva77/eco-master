import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading, SubpageHeader } from "../components/common";
import { useBack } from "../hooks/useBack";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";

// Fixed order (TZ 8.10); the server's JSON does not preserve key order.
const SECTIONS = [
  { key: "problem", icon: "😟" },
  { key: "cause", icon: "🔍" },
  { key: "effect", icon: "⚠️" },
  { key: "solution", icon: "💡" },
  { key: "action", icon: "🙋" },
] as const;

export function CardScreen() {
  const { slug = "" } = useParams();
  const { t } = useTranslation();
  const tr = useTr();
  const back = useBack("/learn");
  const data = useLoad(() => api.card(slug), [slug]);
  const sections = tr<Record<string, string>>(data.data?.sections);

  return (
    <main className="screen">
      <SubpageHeader onBack={back} title={data.data && tr(data.data.title)} />
      {data.loading && !data.data && <InlineLoading />}
      {data.error !== undefined && !data.data && <InlineError error={data.error} onRetry={data.reload} />}
      {sections && (
        <ol className="card-chain">
          {SECTIONS.filter(({ key }) => sections[key]).map(({ key, icon }) => (
            <li key={key} className={`card card-chain__item card-chain__item--${key}`}>
              <h2>
                <span aria-hidden="true">{icon}</span> {t(`card.${key}`)}
              </h2>
              <p>{sections[key]}</p>
            </li>
          ))}
        </ol>
      )}
    </main>
  );
}
