import { ChevronRight, Globe2 } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { tint, TopBar } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";

export function LearnScreen() {
  const { t } = useTranslation();
  const tr = useTr();
  const data = useLoad(() => Promise.all([api.categories(), api.cards()]), []);
  const [categories, cards] = data.data ?? [[], []];

  return (
    <main className="screen screen--with-nav">
      <TopBar subtitle={t("nav.learn")} />
      <h1>{t("learn.title")}</h1>
      <p className="hint" style={{ marginTop: 4 }}>
        {t("learn.subtitle")}
      </p>
      {data.loading && !data.data && <InlineLoading />}
      {data.error !== undefined && !data.data && <InlineError error={data.error} onRetry={data.reload} />}

      {data.data && (
        <>
          <section className="section">
            <div className="section-head">
              <h2>{t("learn.wasteTypes")}</h2>
            </div>
            <ul className="list">
              {categories
                .filter((c) => c.has_projects)
                .map((category) => (
                  <li key={category.code}>
                    <Link className="list-row" to={`/learn/${category.code}`}>
                      <span className="icon-tile" style={tint(category.color)} aria-hidden="true">
                        {category.icon}
                      </span>
                      <span className="list-row__text">
                        <strong>{tr(category.name)}</strong>
                        <span className="hint small">{t("learn.projects", { count: category.project_count })}</span>
                      </span>
                      <ChevronRight className="list-row__chevron" size={20} />
                    </Link>
                  </li>
                ))}
            </ul>
          </section>

          {cards.length > 0 && (
            <section className="section">
              <div className="section-head">
                <h2>{t("learn.cards")}</h2>
              </div>
              <ul className="list">
                {cards.map((card) => (
                  <li key={card.slug}>
                    <Link className="list-row" to={`/cards/${card.slug}`}>
                      <span className="icon-tile icon-tile--sky" aria-hidden="true">
                        <Globe2 size={22} />
                      </span>
                      <span className="list-row__text">
                        <strong>{tr(card.title)}</strong>
                        <span className="hint small">{t("learn.cardHint")}</span>
                      </span>
                      <ChevronRight className="list-row__chevron" size={20} />
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </main>
  );
}
