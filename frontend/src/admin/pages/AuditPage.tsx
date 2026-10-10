import { useEffect, useState } from "react";

import { adminApi, errorText, type AuditRow } from "../api";
import { fmtDateTime, Loading, PageHead } from "../ui";

const ACTIONS: Record<string, string> = {
  "auth.login": "Kirdi",
  "auth.locked": "Hisob vaqtincha bloklandi (noto'g'ri urinishlar)",
  "auth.password_changed": "Parolini o'zgartirdi",
  "admin.create": "Admin qo'shdi",
  "admin.update": "Adminni o'zgartirdi",
  "admin.reset_2fa": "2FA ni tikladi",
  "admin.set_password": "Vaqtinchalik parol berdi",
  "content.create": "Kontent qo'shdi",
  "content.update": "Kontentni tahrirladi",
  "content.status": "Holatini o'zgartirdi",
  "content.delete": "Qoralamani o'chirdi",
  "schedule.set": "Jadvalni o'zgartirdi",
  "user.block": "Bloklandi",
  "user.unblock": "Blokdan chiqarildi",
  "user.nickname_hide": "Taxallus yashirildi",
  "user.nickname_show": "Taxallus ko'rsatildi",
  "user.nickname_reset": "Taxallusni o'zgartirish talab qilindi",
  "user.void_points": "Ballar bekor qilindi",
  "report.resolve": "Shikoyatlar hal qilindi",
  "word.add": "So'z qo'shildi",
  "word.delete": "So'z o'chirildi",
};

function details(row: AuditRow): string {
  if (!row.details) return "";
  return Object.entries(row.details)
    .filter(([, v]) => v !== null && v !== undefined && v !== "")
    .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : typeof v === "object" ? JSON.stringify(v) : String(v)}`)
    .join(" · ");
}

/** Who did what and when (TZ 8.12). */
export function AuditPage() {
  const [rows, setRows] = useState<AuditRow[]>([]);
  const [next, setNext] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load(before: number | null) {
    setLoading(true);
    try {
      const page = await adminApi.audit(before);
      setRows((prev) => (before ? [...prev, ...page.rows] : page.rows));
      setNext(page.next_before_id ?? null);
      setError(null);
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load(null);
  }, []);

  return (
    <>
      <PageHead title="Audit jurnali" />
      <div className="a-table-wrap">
        <table className="a-table">
          <thead>
            <tr>
              <th>Vaqt</th>
              <th>Kim</th>
              <th>Nima qildi</th>
              <th>Obyekt</th>
              <th>Tafsilot</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td className="a-small" style={{ whiteSpace: "nowrap" }}>
                  {fmtDateTime(r.created_at)}
                </td>
                <td>{r.admin_name ?? "—"}</td>
                <td>{ACTIONS[r.action] ?? r.action}</td>
                <td className="a-mono">
                  {r.object_type}
                  {r.object_id ? ` #${r.object_id}` : ""}
                </td>
                <td className="a-small a-muted">{details(r)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {loading && <Loading />}
        {error && <p className="a-empty a-error">{error}</p>}
      </div>
      {next !== null && !loading && (
        <button type="button" className="a-btn a-btn--ghost" style={{ marginTop: 12 }} onClick={() => void load(next)}>
          Yana yuklash
        </button>
      )}
    </>
  );
}
