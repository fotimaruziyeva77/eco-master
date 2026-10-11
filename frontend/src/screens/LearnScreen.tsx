import { ChevronRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { Emoji } from "../components/Emoji";
import { tint, TopBar } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";

/** Waste types as big picture tiles, then the knowledge cards. */
export function LearnScreen() {
  const { t } = useTranslation();
  const tr = useTr();
  const data = useLoad(() => Promise.all([api.categories(), api.cards()]), []);
  const [categories, cards] = data.data ?? [[], []];

  return (
    <main className="screen screen--with-nav">
      <TopBar />
      <h1>{t("learn.title")}</h1>
      {data.loading && !data.data && <InlineLoading />}
      {data.error !== undefined && !data.data && <InlineError error={data.error} onRetry={data.reload} />}

      {data.data && (
        <>
          <section className="section">
            <div className="tile-grid">
              {categories
                .filter((c) => c.has_projects && c.project_count > 0)
                .map((category) => (
                  <Link key={category.code} className="tile" to={`/learn/${category.code}`} style={tint(category.color, "22")}>
                    <span className="tile__icon" aria-hidden="true">
                      <Emoji char={category.icon} />
                    </span>
                    <strong>{tr(category.name)}</strong>
                    <span className="tile__count">{t("learn.projects", { count: category.project_count })}</span>
                  </Link>
                ))}
            </div>
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
                        {card.image_url ? <img className="icon-tile__img" src={card.image_url} alt="" /> : <Emoji char="🌍" />}
                      </span>
                      <span className="list-row__text">
                        <strong>{tr(card.title)}</strong>
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
