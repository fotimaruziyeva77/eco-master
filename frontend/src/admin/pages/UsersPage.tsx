import { Search } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, type UserRow } from "../api";
import { fmtDateTime, LoadError, Loading, PageHead, PATH_LABEL } from "../ui";

const FILTERS = [
  ["all", "Hammasi"],
  ["reported", "Shikoyat qilinganlar"],
  ["flagged", "Shubhali"],
  ["blocked", "Bloklanganlar"],
  ["hidden", "Taxallusi yashirilganlar"],
] as const;

export function UserStateChips({ user }: { user: UserRow }) {
  return (
    <span className="a-row" style={{ gap: 4 }}>
      {user.is_blocked && <span className="a-pill a-pill--danger">Bloklangan</span>}
      {user.nickname_hidden && <span className="a-pill a-pill--warn">Yashirin</span>}
      {user.open_reports > 0 && <span className="a-pill a-pill--danger">{user.open_reports} shikoyat</span>}
      {!user.onboarding_done && <span className="a-pill a-pill--draft">Ro'yxatdan o'tmoqda</span>}
    </span>
  );
}

export function UsersPage() {
  const navigate = useNavigate();
  const [filter, setFilter] = useState<(typeof FILTERS)[number][0]>("all");
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);
  const users = useLoad(() => adminApi.users(query, filter), [query, filter]);

  return (
    <>
      <PageHead title="Foydalanuvchilar" />
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
            style={{ width: 280 }}
            placeholder="Taxallus, ichki ID yoki Telegram ID"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>
      {users.loading && !users.data && <Loading />}
      {users.error !== undefined && !users.data && <LoadError error={users.error} onRetry={users.reload} />}
      {users.data && (
        <div className="a-table-wrap">
          <table className="a-table">
            <thead>
              <tr>
                <th className="num">ID</th>
                <th>Taxallus</th>
                <th>Yo'l</th>
                <th>Til</th>
                <th className="num">Ball</th>
                <th className="num">Streak</th>
                <th>Oxirgi faollik</th>
                <th>Holat</th>
              </tr>
            </thead>
            <tbody>
              {users.data.map((u) => (
                <tr key={u.id} className="a-click" onClick={() => navigate(`/users/${u.id}`)}>
                  <td className="num a-muted">{u.id}</td>
                  <td>
                    <strong>{u.nickname ? `@${u.nickname}` : "—"}</strong>
                  </td>
                  <td>{u.path ? PATH_LABEL[u.path] : "—"}</td>
                  <td>{u.language.toUpperCase()}</td>
                  <td className="num">{u.points_total}</td>
                  <td className="num">{u.streak_current}</td>
                  <td className="a-small a-muted">{fmtDateTime(u.last_active_at)}</td>
                  <td>
                    <UserStateChips user={u} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {users.data.length === 0 && <p className="a-empty">Hech kim topilmadi.</p>}
        </div>
      )}
    </>
  );
}
