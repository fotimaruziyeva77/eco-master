import { useState } from "react";
import { Link } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, type ReportGroup } from "../api";
import { ConfirmModal, fmtDateTime, LoadError, Loading, PageHead, useToast } from "../ui";

type Action = "dismiss" | "hide" | "reset" | "block";
const ACTIONS: { action: Action; label: string; kind: string; text: string }[] = [
  { action: "dismiss", label: "Rad etish", kind: "a-btn a-btn--ghost a-btn--sm", text: "Shikoyatlar asossiz deb yopiladi." },
  { action: "hide", label: "Taxallusni yashirish", kind: "a-btn a-btn--soft a-btn--sm", text: "Taxallus reytingda ko'rinmaydi." },
  { action: "reset", label: "O'zgartirishni talab qilish", kind: "a-btn a-btn--amber a-btn--sm", text: "Taxallus o'chiriladi, foydalanuvchi yangisini tanlaydi." },
  { action: "block", label: "Bloklash", kind: "a-btn a-btn--danger a-btn--sm", text: "Foydalanuvchi ilovani ocholmaydi." },
];

/** Complaints about nicknames on the leaderboard (TZ 8.7, 8.12). */
export function ReportsPage() {
  const toast = useToast();
  const [tab, setTab] = useState<"open" | "history">("open");
  const open = useLoad(() => adminApi.openReports(), []);
  const history = useLoad(() => (tab === "history" ? adminApi.reportHistory() : Promise.resolve([])), [tab]);
  const [pending, setPending] = useState<{ group: ReportGroup; action: (typeof ACTIONS)[number] } | null>(null);

  return (
    <>
      <PageHead title="Shikoyatlar" />
      <div className="a-toolbar">
        <div className="a-tabs">
          <button type="button" className={tab === "open" ? "a-tab active" : "a-tab"} onClick={() => setTab("open")}>
            Ochiq <small>{open.data?.length ?? ""}</small>
          </button>
          <button type="button" className={tab === "history" ? "a-tab active" : "a-tab"} onClick={() => setTab("history")}>
            Ko'rib chiqilgan
          </button>
        </div>
      </div>

      {tab === "open" && (
        <>
          {open.loading && !open.data && <Loading />}
          {open.error !== undefined && !open.data && <LoadError error={open.error} onRetry={open.reload} />}
          {open.data?.length === 0 && <p className="a-empty">Ochiq shikoyat yo'q. 🎉</p>}
          <div className="a-stack">
            {open.data?.map((group) => (
              <section key={group.target.id} className="a-card">
                <div className="a-row" style={{ marginBottom: 10 }}>
                  <Link to={`/users/${group.target.id}`} style={{ marginRight: "auto" }}>
                    <strong style={{ fontSize: 17 }}>@{group.target.nickname ?? "—"}</strong>
                  </Link>
                  <span className="a-pill a-pill--danger">{group.count} ta shikoyat</span>
                </div>
                <p className="a-small a-muted" style={{ marginBottom: 12 }}>
                  Birinchisi {fmtDateTime(group.first_at)}, oxirgisi {fmtDateTime(group.last_at)} · ID {group.target.id} · {group.target.points_total} ball
                </p>
                <div className="a-row">
                  {ACTIONS.map((a) => (
                    <button key={a.action} type="button" className={a.kind} onClick={() => setPending({ group, action: a })}>
                      {a.label}
                    </button>
                  ))}
                </div>
              </section>
            ))}
          </div>
        </>
      )}

      {tab === "history" && (
        <>
          {history.loading && !history.data && <Loading />}
          {history.data && (
            <div className="a-table-wrap">
              <table className="a-table">
                <thead>
                  <tr>
                    <th>Kelgan</th>
                    <th>Kim haqida</th>
                    <th>Qaror</th>
                    <th>Kim hal qildi</th>
                  </tr>
                </thead>
                <tbody>
                  {history.data.map((r) => (
                    <tr key={r.id}>
                      <td className="a-small">{fmtDateTime(r.created_at)}</td>
                      <td>
                        <Link to={`/users/${r.target_user_id}`}>@{r.target_nickname ?? r.target_user_id}</Link>
                      </td>
                      <td>{r.resolution}</td>
                      <td className="a-small">
                        {r.resolved_by ?? "—"} · {fmtDateTime(r.resolved_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {history.data.length === 0 && <p className="a-empty">Hali yo'q.</p>}
            </div>
          )}
        </>
      )}

      {pending && (
        <ConfirmModal
          title={`@${pending.group.target.nickname ?? ""}: ${pending.action.label.toLowerCase()}`}
          text={`${pending.action.text} Ushbu foydalanuvchi haqidagi ${pending.group.count} ta shikoyat yopiladi.`}
          confirm={pending.action.label}
          danger={pending.action.action === "block"}
          reason
          onClose={() => setPending(null)}
          onConfirm={async (note) => {
            await adminApi.resolve(pending.group.target.id, pending.action.action, note);
            toast("Shikoyatlar yopildi");
            open.reload();
          }}
        />
      )}
    </>
  );
}
