import { Plus, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, type ContentStatus } from "../api";
import { fmtDateTime, LoadError, Loading, PageHead, STATUS_LABEL, StatusPill } from "../ui";

const STATUSES: ContentStatus[] = ["draft", "review", "published", "archived"];

export function ContentListPage() {
  const { type = "" } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<ContentStatus | null>(null);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");

  useEffect(() => {
    setStatus(null);
    setSearch("");
  }, [type]);
  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  const types = useLoad(() => adminApi.contentTypes(), [type]);
  const info = types.data?.find((t) => t.key === type);
  const rows = useLoad(() => adminApi.contentList(type, status, query), [type, status, query]);

  return (
    <>
      <PageHead title={info?.title ?? "Kontent"}>
        <Link className="a-btn" to={`/content/${type}/new`}>
          <Plus size={16} /> Yangi qo'shish
        </Link>
      </PageHead>

      <div className="a-toolbar">
        {info?.has_status && (
          <div className="a-tabs" role="tablist" aria-label="Holat">
            <button type="button" className={status === null ? "a-tab active" : "a-tab"} onClick={() => setStatus(null)}>
              Hammasi <small>{info.counts.all ?? 0}</small>
            </button>
            {STATUSES.map((s) => (
              <button key={s} type="button" className={status === s ? "a-tab active" : "a-tab"} onClick={() => setStatus(s)}>
                {STATUS_LABEL[s]} <small>{info.counts[s] ?? 0}</small>
              </button>
            ))}
          </div>
        )}
        <label className="a-row" style={{ marginLeft: "auto", flexWrap: "nowrap" }}>
          <Search size={16} className="a-muted" aria-hidden="true" />
          <input
            className="a-input"
            style={{ width: 260 }}
            placeholder="Qidirish (uch tilda)"
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
                <th>Nomi</th>
                {info?.has_status && <th>Holat</th>}
                <th>Tekshiruv</th>
                <th>O'zgartirilgan</th>
              </tr>
            </thead>
            <tbody>
              {rows.data.map((row) => (
                <tr key={row.id} className="a-click" onClick={() => navigate(`/content/${type}/${row.id}`)}>
                  <td className="a-title-cell">
                    <Link to={`/content/${type}/${row.id}`} onClick={(e) => e.stopPropagation()} style={{ textDecoration: "none" }}>
                      <strong>{row.title}</strong>
                    </Link>
                    <span className="a-muted a-small">{row.subtitle}</span>
                  </td>
                  {info?.has_status && (
                    <td>
                      <StatusPill status={row.status} />
                    </td>
                  )}
                  <td>
                    <span className="a-row" style={{ gap: 4 }}>
                      {row.errors > 0 && <span className="a-pill a-pill--danger">{row.errors} xato</span>}
                      {row.warnings > 0 && <span className="a-pill a-pill--warn">{row.warnings} ogohlantirish</span>}
                      {row.errors === 0 && row.warnings === 0 && <span className="a-pill a-pill--ok">✓ tayyor</span>}
                    </span>
                  </td>
                  <td className="a-muted a-small">{fmtDateTime(row.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {rows.data.length === 0 && <p className="a-empty">Hech narsa topilmadi.</p>}
        </div>
      )}
    </>
  );
}
