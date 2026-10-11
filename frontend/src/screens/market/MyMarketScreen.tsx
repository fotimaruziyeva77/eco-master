import { ChevronRight, Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { api, type MyListing, type MyRequest } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { SubpageHeader } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { useTr } from "../../i18n/tr";
import { CodeBox, StatusChip, useShortDate } from "./parts";

/** The user's own listings and the things they asked for. */
export function MyMarketScreen() {
  const { t } = useTranslation();
  const back = useBack("/market");
  const [tab, setTab] = useState<"listings" | "requests">("listings");
  const listings = useLoad(() => api.myListings(), []);
  const requests = useLoad(() => (tab === "requests" ? api.myRequests() : Promise.resolve(null)), [tab]);

  return (
    <main className="screen stack stack--lg">
      <SubpageHeader onBack={back} title={t("market.title")} />
      <div className="tabs" role="tablist">
        {(["listings", "requests"] as const).map((value) => (
          <button
            key={value}
            type="button"
            role="tab"
            aria-selected={tab === value}
            className={tab === value ? "tabs__item is-active" : "tabs__item"}
            onClick={() => setTab(value)}
          >
            {t(value === "listings" ? "market.mine" : "market.myRequests")}
          </button>
        ))}
      </div>

      {tab === "listings" && (
        <>
          {listings.loading && !listings.data && <InlineLoading />}
          {listings.error !== undefined && !listings.data && (
            <InlineError error={listings.error} onRetry={listings.reload} />
          )}
          {listings.data?.length === 0 && <p className="empty">{t("market.emptyMine")}</p>}
          <ul className="list">
            {listings.data?.map((item) => (
              <li key={item.id}>
                <ListingRow item={item} />
              </li>
            ))}
          </ul>
          <Link to="/market/new" className="btn btn--block">
            <Plus size={18} aria-hidden="true" /> {t("market.add")}
          </Link>
        </>
      )}

      {tab === "requests" && (
        <>
          {requests.loading && !requests.data && <InlineLoading />}
          {requests.error !== undefined && !requests.data && (
            <InlineError error={requests.error} onRetry={requests.reload} />
          )}
          {requests.data?.length === 0 && <p className="empty">{t("market.emptyRequests")}</p>}
          <ul className="list">
            {requests.data?.map((item) => (
              <li key={item.id}>
                <RequestRow item={item} />
              </li>
            ))}
          </ul>
        </>
      )}
    </main>
  );
}

function Thumb({ url }: { url: string | null | undefined }) {
  return <span className="thumb">{url ? <img src={url} alt="" loading="lazy" /> : <Emoji char="🌱" />}</span>;
}

function ListingRow({ item }: { item: MyListing }) {
  const { t } = useTranslation();
  return (
    <Link to={`/market/${item.id}`} className="list-row">
      <Thumb url={item.thumb_url} />
      <span className="list-row__text">
        <strong>{item.title}</strong>
        <span className="row row--wrap" style={{ gap: 6 }}>
          <StatusChip status={item.status} />
          {item.waiting_requests > 0 && (
            <span className="chip chip--sm chip--amber">{t("market.waitingRequests", { count: item.waiting_requests })}</span>
          )}
        </span>
      </span>
      <ChevronRight className="list-row__chevron" size={20} aria-hidden="true" />
    </Link>
  );
}

function RequestRow({ item }: { item: MyRequest }) {
  const { t } = useTranslation();
  const tr = useTr();
  const date = useShortDate();
  return (
    <div className="card stack">
      <Link to={`/market/${item.listing_id}`} className="row" style={{ color: "inherit", textDecoration: "none" }}>
        <Thumb url={item.thumb_url} />
        <span className="list-row__text">
          <strong>{item.title}</strong>
          <span className="hint small">{t(`market.requestStatus.${item.status}`)}</span>
        </span>
        <ChevronRight className="list-row__chevron" size={20} aria-hidden="true" />
      </Link>
      {item.status === "at_point" && item.code && (
        <>
          <p className="text-2">{t("market.handover.pickText", { date: date(item.deadline) })}</p>
          <CodeBox code={item.code} />
          {item.point && (
            <p className="hint small">
              {tr(item.point.name)} — {tr(item.point.address)}
            </p>
          )}
        </>
      )}
    </div>
  );
}
