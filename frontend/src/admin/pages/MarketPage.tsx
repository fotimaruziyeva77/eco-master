import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, type MarketFilter, type MarketReason, type MarketRow } from "../api";
import { fmtDateTime, LoadError, Loading, PageHead } from "../ui";

export const LISTING_STATUS: Record<MarketRow["status"], [string, string]> = {
  pending: ["Tekshiruvda", "a-pill a-pill--review"],
  approved: ["Bozorda", "a-pill a-pill--published"],
  rejected: ["Qaytarilgan", "a-pill a-pill--danger"],
  reserved: ["Band qilingan", "a-pill a-pill--warn"],
  at_point: ["Topshirish joyida", "a-pill a-pill--warn"],
  given: ["Berilgan", "a-pill a-pill--archived"],
  hidden: ["Yashirilgan", "a-pill a-pill--danger"],
};

export const KIND_LABEL: Record<MarketRow["kind"], string> = {
  handmade: "O'zi yasagan",
  unneeded: "Keraksiz narsa",
};

/** Reasons a moderator can give; the child gets them in their language (bot texts). */
export const REASONS: [MarketReason, string][] = [
  ["personal_info", "Shaxsiy ma'lumot (ism, manzil, telefon, maktab)"],
  ["face", "Rasmda odam yuzi bor"],
  ["not_eco", "Bozor mavzusiga mos emas"],
  ["forbidden", "Taqiqlangan narsa"],
  ["bad_photo", "Rasm sifatsiz"],
  ["other", "Boshqa sabab"],
];

const FILTERS: [MarketFilter, string][] = [
  ["pending", "Tekshiruvda"],
  ["reported", "Shikoyat qilingan"],
  ["handover", "Topshirilmoqda"],
  ["approved", "Bozorda"],
  ["rejected", "Qaytarilgan"],
  ["hidden", "Yashirilgan"],
  ["all", "Hammasi"],
];

export function StatusBadge({ status }: { status: MarketRow["status"] }) {
  const [label, className] = LISTING_STATUS[status];
  return <span className={className}>{label}</span>;
}

/** Market listings: the review queue first (TZ 8.12 moderation, phase 9). */
export function MarketPage() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<MarketFilter>("pending");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);
  const rows = useLoad(() => adminApi.market(filter, query), [filter, query]);

  return (
    <>
      <PageHead title="Bozor: e'lonlar" />
      <p className="a-help" style={{ marginBottom: 14 }}>
        Har bir e'lon tasdiqlangandan keyingina bozorda ko'rinadi. Rasmda yuz, ism, manzil, maktab nomi yoki telefon
        bo'lmasligi kerak; ovqat, dori, o'tkir va xavfli narsalar, batareya va elektronika qabul qilinmaydi.
      </p>
      <div className="a-toolbar">
        <div className="a-tabs">
          {FILTERS.map(([value, label]) => (
            <button key={value} type="button" className={filter === value ? "a-tab active" : "a-tab"} onClick={() => setFilter(value)}>
              {label}
            </button>
          ))}
        </div>
        <label className="a-row" style={{ marginLeft: "auto", flexWrap: "nowrap" }}>
          <Search size={16} className="a-muted" aria-hidden="true" />
          <input
            className="a-input"
            style={{ width: 240 }}
            placeholder="Nomi, taxallus yoki ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>
      {rows.loading && !rows.data && <Loading />}
      {rows.error !== undefined && !rows.data && <LoadError error={rows.error} onRetry={rows.reload} />}
      {rows.data && (
        <div className="a-table-wrap">
          <table className="a-table">
            <thead>
              <tr>
                <th />
                <th>Nomi</th>
                <th>Turi</th>
                <th>Muallif</th>
                <th>Yuborilgan</th>
                <th>Holat</th>
              </tr>
            </thead>
            <tbody>
              {rows.data.map((row) => (
                <tr key={row.id} className="a-click" onClick={() => navigate(`/market/${row.id}`)}>
                  <td style={{ width: 64 }}>
                    {row.thumb_url ? <img className="a-thumb" src={row.thumb_url} alt="" loading="lazy" /> : "—"}
                  </td>
                  <td>
                    <strong>{row.title}</strong>
                    <div className="a-small a-muted">ID {row.id}</div>
                  </td>
                  <td>
                    {KIND_LABEL[row.kind]}
                    {row.giveaway && <div className="a-small a-muted">beriladi</div>}
                  </td>
                  <td>{row.owner_nickname ? `@${row.owner_nickname}` : "—"}</td>
                  <td className="a-small a-muted">{fmtDateTime(row.submitted_at)}</td>
                  <td>
                    <span className="a-row" style={{ gap: 4 }}>
                      <StatusBadge status={row.status} />
                      {row.reports_open > 0 && <span className="a-pill a-pill--danger">{row.reports_open} shikoyat</span>}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.data.length === 0 && <p className="a-empty">Bu yerda hozircha hech narsa yo'q.</p>}
        </div>
      )}
    </>
  );
}
