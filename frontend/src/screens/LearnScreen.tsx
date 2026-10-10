import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";

export function LearnScreen() {
  const { t } = useTranslation();
  const tr = useTr();
  const data = useLoad(() => Promise.all([api.categories(), api.cards()]), []);

  return (
    <main className="screen screen--with-nav">
      <h1>{t("learn.title")}</h1>
      {data.loading && !data.data && <InlineLoading />}
      {data.error !== undefined && !data.data && <InlineError error={data.error} onRetry={data.reload} />}

      {data.data && (
        <>
          <h2 className="section-title">{t("learn.wasteTypes")}</h2>
          <ul className="list">
            {data.data[0]
              .filter((c) => c.has_projects)
              .map((category) => (
                <li key={category.code}>
                  <Link className="list-row" to={`/learn/${category.code}`}>
                    <span className="list-row__icon" style={{ background: category.color }} aria-hidden="true">
                      {category.icon}
                    </span>
                    <span className="list-row__text">
                      <strong>{tr(category.name)}</strong>
                      <span className="hint">{t("learn.projects", { count: category.project_count })}</span>
                    </span>
                    <span className="list-row__chevron" aria-hidden="true">
                      ›
                    </span>
                  </Link>
                </li>
              ))}
          </ul>

          {data.data[1].length > 0 && (
            <>
              <h2 className="section-title">{t("learn.cards")}</h2>
              <ul className="list">
                {data.data[1].map((card) => (
                  <li key={card.slug}>
                    <Link className="list-row" to={`/cards/${card.slug}`}>
                      <span className="list-row__icon list-row__icon--soft" aria-hidden="true">
                        🌍
                      </span>
                      <span className="list-row__text">
                        <strong>{tr(card.title)}</strong>
                      </span>
                      <span className="list-row__chevron" aria-hidden="true">
                        ›
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}
    </main>
  );
}
