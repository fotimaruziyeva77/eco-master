import { Heart, PackageCheck, Plus, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api, type ListingCard, type ListingKind } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { TopBar } from "../../components/ui";
import { useLoad } from "../../hooks/useLoad";
import { useTr } from "../../i18n/tr";
import { haptic } from "../../telegram";
import { useCategoryLabel } from "./parts";

const FILTERS: (ListingKind | null)[] = [null, "handmade", "unneeded"];

/** Eco market (phase 9): approved listings, newest first. */
export function MarketScreen() {
  const { t } = useTranslation();
  const tr = useTr();
  const [kind, setKind] = useState<ListingKind | null>(null);
  const [point, setPoint] = useState<number | null>(null);
  const [items, setItems] = useState<ListingCard[]>([]);
  const [next, setNext] = useState<number | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const page = useLoad(() => api.market({ kind, point }), [kind, point]);
  const points = useLoad(() => api.marketPoints(), []);
  const categories = useLoad(() => api.categories(), []);
  const label = useCategoryLabel(categories.data);

  useEffect(() => {
    if (!page.data) return;
    setItems(page.data.items);
    setNext(page.data.next_offset ?? null);
  }, [page.data]);

  async function more() {
    if (next === null) return;
    setLoadingMore(true);
    try {
      const data = await api.market({ kind, point, offset: next });
      setItems((prev) => [...prev, ...data.items]);
      setNext(data.next_offset ?? null);
    } finally {
      setLoadingMore(false);
    }
  }

  return (
    <main className="screen screen--with-nav screen--with-fab stack stack--lg">
      <TopBar />

      <div className="row row--between">
        <h1>{t("market.title")}</h1>
        <Link to="/market/mine" className="btn btn--soft btn--sm">
          <UserRound size={16} aria-hidden="true" /> {t("market.mine")}
        </Link>
      </div>

      <div className="segmented" role="tablist">
        {FILTERS.map((value) => (
          <button
            key={value ?? "all"}
            type="button"
            role="tab"
            aria-selected={kind === value}
            className={kind === value ? "segmented__item is-active" : "segmented__item"}
            onClick={() => {
              haptic.tap();
              setKind(value);
            }}
          >
            {t(`market.filters.${value ?? "all"}`)}
          </button>
        ))}
      </div>

      {points.data && points.data.length > 1 && (
        <select
          className="select"
          aria-label={t("market.point")}
          value={point ?? ""}
          onChange={(e) => setPoint(e.target.value ? Number(e.target.value) : null)}
        >
          <option value="">{t("market.allPoints")}</option>
          {points.data.map((p) => (
            <option key={p.id} value={p.id}>
              {tr(p.name)}
            </option>
          ))}
        </select>
      )}

      {page.loading && !page.data && <InlineLoading />}
      {page.error !== undefined && !page.data && <InlineError error={page.error} onRetry={page.reload} />}
      {page.data && items.length === 0 && <p className="empty">{t("market.empty")}</p>}

      <ul className="market-grid">
        {items.map((item) => (
          <li key={item.id}>
            <Link to={`/market/${item.id}`} className="market-card">
              <span className="market-card__photo">
                {item.thumb_url ? <img src={item.thumb_url} alt="" loading="lazy" /> : <Emoji char="🌱" />}
                {item.ready_at_point && (
                  <span className="market-card__flag" title={t("market.readyAtPoint")}>
                    <PackageCheck size={14} aria-hidden="true" />
                  </span>
                )}
              </span>
              <span className="market-card__body">
                <strong>{item.title}</strong>
                <span className="hint small">{label(item.kind, item.category)}</span>
                <span className="market-card__foot">
                  <span className={item.giveaway ? "chip chip--sm" : "chip chip--sm chip--neutral"}>
                    {item.giveaway ? t("market.giveaway") : t("market.showOnly")}
                  </span>
                  <span className="hint small row" aria-label={t("market.likesCount", { count: item.likes })}>
                    <Heart size={14} aria-hidden="true" fill={item.liked ? "currentColor" : "none"} /> {item.likes}
                  </span>
                </span>
              </span>
            </Link>
          </li>
        ))}
      </ul>

      {next !== null && (
        <button type="button" className="btn btn--soft btn--block" disabled={loadingMore} onClick={() => void more()}>
          {t("market.more")}
        </button>
      )}

      <Link to="/market/new" className="fab" aria-label={t("market.add")}>
        <Plus size={22} aria-hidden="true" /> {t("market.add")}
      </Link>
    </main>
  );
}
