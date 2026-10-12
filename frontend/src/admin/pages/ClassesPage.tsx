import { Search, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, type AdminClass } from "../api";
import { ConfirmModal, fmtDate, LoadError, Loading, PageHead, useToast } from "../ui";

/** Teachers' classes (stage 5): who made them, how many pupils; removing an offensive one. */
export function ClassesPage() {
  const toast = useToast();
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [removing, setRemoving] = useState<AdminClass | null>(null);
  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);
  const classes = useLoad(() => adminApi.classes(query), [query]);

  return (
    <>
      <PageHead title="Sinflar" />
      <p className="a-help" style={{ marginBottom: 12 }}>
        O'qituvchilar ochgan sinflar. O'quvchilar QR-kod bilan o'zlari qo'shiladi va istalgan vaqtda chiqadi;
        o'qituvchi faqat taxallus, daraja va ballarni ko'radi.
      </p>
      <div className="a-toolbar">
        <label className="a-row" style={{ marginLeft: "auto", flexWrap: "nowrap" }}>
          <Search size={16} className="a-muted" aria-hidden="true" />
          <input
            className="a-input"
            style={{ width: 280 }}
            placeholder="Sinf nomi, o'qituvchi taxallusi yoki kod"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </label>
      </div>
      {classes.loading && !classes.data && <Loading />}
      {classes.error !== undefined && !classes.data && <LoadError error={classes.error} onRetry={classes.reload} />}
      {classes.data && (
        <div className="a-table-wrap">
          <table className="a-table">
            <thead>
              <tr>
                <th>Sinf</th>
                <th>Kod</th>
                <th>O'qituvchi</th>
                <th className="num">O'quvchilar</th>
                <th className="num">Vazifalar</th>
                <th>Ochilgan</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {classes.data.map((c) => (
                <tr key={c.id}>
                  <td>
                    <strong>{c.name}</strong>
                  </td>
                  <td className="a-mono">{c.code}</td>
                  <td>
                    <Link to={`/users/${c.teacher_id}`}>{c.teacher_nickname ? `@${c.teacher_nickname}` : `#${c.teacher_id}`}</Link>
                  </td>
                  <td className="num">{c.member_count}</td>
                  <td className="num">{c.task_count}</td>
                  <td className="a-small a-muted">{fmtDate(c.created_at)}</td>
                  <td>
                    <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => setRemoving(c)}>
                      <Trash2 size={14} /> O'chirish
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {classes.data.length === 0 && <p className="a-empty">Sinf topilmadi.</p>}
        </div>
      )}
      {removing && (
        <ConfirmModal
          title={`«${removing.name}» sinfini o'chirish`}
          text="Sinf va uning vazifalari o'chiriladi; o'quvchilar ilovada qoladi. Masalan, nomi haqoratli bo'lsa."
          confirm="O'chirish"
          danger
          onClose={() => setRemoving(null)}
          onConfirm={async () => {
            await adminApi.deleteClass(removing.id);
            toast("O'chirildi");
            classes.reload();
          }}
        />
      )}
    </>
  );
}
