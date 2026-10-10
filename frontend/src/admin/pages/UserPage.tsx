import { ArrowLeft, Ban, EyeOff, Eye, PenOff, Undo2 } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, type UserDetail } from "../api";
import { ConfirmModal, fmtDate, fmtDateTime, LoadError, Loading, PageHead, PATH_LABEL, useToast } from "../ui";
import { UserStateChips } from "./UsersPage";

const ACTION_LABEL: Record<string, string> = {
  project_done: "Loyiha bajarildi",
  quiz_correct: "Viktorina: to'g'ri javob",
  game_correct: "O'yin: to'g'ri saralash",
  daily_task: "Kunlik topshiriq",
  streak_bonus: "Streak bonusi",
  voided: "Bekor qilingan",
};

type Dialog = "block" | "unblock" | "hide" | "show" | "reset" | "void" | null;

export function UserPage() {
  const { id = "" } = useParams();
  const toast = useToast();
  const loaded = useLoad(() => adminApi.user(Number(id)), [id]);
  const [override, setOverride] = useState<UserDetail | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [dialog, setDialog] = useState<Dialog>(null);

  const user = override?.id === Number(id) ? override : loaded.data;
  if (loaded.error !== undefined && !user) return <LoadError error={loaded.error} onRetry={loaded.reload} />;
  if (!user) return <Loading />;

  const apply = (next: UserDetail, message: string) => {
    setOverride(next);
    setSelected(new Set());
    toast(message);
  };
  const toggle = (rowId: number) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(rowId)) next.delete(rowId);
      else next.add(rowId);
      return next;
    });

  const counts = user.counts;
  return (
    <>
      <div className="a-row" style={{ marginBottom: 8 }}>
        <Link to="/users" className="a-btn a-btn--ghost a-btn--sm">
          <ArrowLeft size={14} /> Foydalanuvchilar
        </Link>
      </div>
      <PageHead title={user.nickname ? `@${user.nickname}` : `Foydalanuvchi #${user.id}`}>
        <UserStateChips user={user} />
      </PageHead>

      <div className="a-toolbar">
        {user.is_blocked ? (
          <button type="button" className="a-btn a-btn--soft" onClick={() => setDialog("unblock")}>
            <Undo2 size={16} /> Blokdan chiqarish
          </button>
        ) : (
          <button type="button" className="a-btn a-btn--danger" onClick={() => setDialog("block")}>
            <Ban size={16} /> Bloklash
          </button>
        )}
        {user.nickname &&
          (user.nickname_hidden ? (
            <button type="button" className="a-btn a-btn--ghost" onClick={() => setDialog("show")}>
              <Eye size={16} /> Taxallusni ko'rsatish
            </button>
          ) : (
            <button type="button" className="a-btn a-btn--ghost" onClick={() => setDialog("hide")}>
              <EyeOff size={16} /> Taxallusni yashirish
            </button>
          ))}
        {user.nickname && (
          <button type="button" className="a-btn a-btn--amber" onClick={() => setDialog("reset")}>
            <PenOff size={16} /> Taxallusni majburiy o'zgartirish
          </button>
        )}
      </div>

      <div className="a-grid-2" style={{ marginBottom: 16 }}>
        <section className="a-card">
          <h2>Ma'lumotlar</h2>
          <table className="a-table">
            <tbody>
              <tr><td className="a-muted">Ichki ID</td><td>{user.id}</td></tr>
              <tr><td className="a-muted">Telegram ID</td><td className="a-mono">{user.telegram_id}</td></tr>
              <tr><td className="a-muted">Yo'l / til</td><td>{user.path ? PATH_LABEL[user.path] : "—"} · {user.language.toUpperCase()}</td></tr>
              <tr><td className="a-muted">Manba</td><td>{user.source ?? "to'g'ridan-to'g'ri"}</td></tr>
              <tr><td className="a-muted">Ro'yxatdan o'tgan</td><td>{fmtDateTime(user.created_at)}</td></tr>
              <tr><td className="a-muted">Oxirgi faollik</td><td>{fmtDateTime(user.last_active_at)}</td></tr>
              <tr><td className="a-muted">Eslatmalar</td><td>{user.reminders_enabled ? "yoqilgan" : "o'chirilgan"}{user.write_access ? "" : " (bot yoza olmaydi)"}</td></tr>
            </tbody>
          </table>
        </section>
        <section className="a-card">
          <h2>Natijalar</h2>
          <div className="a-kpis" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
            <div className="a-kpi"><strong>{user.points_total}</strong><span>ball</span></div>
            <div className="a-kpi"><strong>{user.streak_current}</strong><span>streak (eng uzuni {user.streak_best})</span></div>
            <div className="a-kpi"><strong>{counts.project_done ?? 0}</strong><span>loyiha</span></div>
            <div className="a-kpi"><strong>{counts.daily_task ?? 0}</strong><span>topshiriq</span></div>
            <div className="a-kpi"><strong>{counts.quiz_correct ?? 0}</strong><span>to'g'ri javob</span></div>
            <div className="a-kpi"><strong>{counts.game_correct ?? 0}</strong><span>to'g'ri saralash</span></div>
          </div>
          <p className="a-small">
            <span className="a-muted">Nishonlar:</span>{" "}
            {user.badges.length ? user.badges.map((b) => `${b.icon} ${b.name}`).join(", ") : "yo'q"}
          </p>
        </section>
      </div>

      {user.flags.length > 0 && (
        <section className="a-card" style={{ marginBottom: 16 }}>
          <h2>Shubhali faollik</h2>
          <div className="a-issues" style={{ margin: 0 }}>
            {user.flags.map((f, i) => (
              <div key={i} className="a-issue a-issue--error" style={{ cursor: "default" }}>
                {fmtDate(f.day)} — {f.message}
              </div>
            ))}
          </div>
        </section>
      )}

      {user.reports.length > 0 && (
        <section className="a-card" style={{ marginBottom: 16 }}>
          <h2>Shikoyatlar</h2>
          <ul className="a-stack" style={{ margin: 0, paddingLeft: 18 }}>
            {user.reports.map((r) => (
              <li key={r.id} className="a-small">
                {fmtDateTime(r.created_at)} — {r.status === "open" ? <strong>ochiq</strong> : r.resolution}
                {r.resolved_by && <span className="a-muted"> ({r.resolved_by})</span>}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="a-card">
        <div className="a-row" style={{ marginBottom: 12 }}>
          <h2 style={{ margin: 0, marginRight: "auto" }}>Faoliyat jurnali</h2>
          <button type="button" className="a-btn a-btn--danger a-btn--sm" disabled={selected.size === 0} onClick={() => setDialog("void")}>
            Tanlangan ballarni bekor qilish ({selected.size})
          </button>
        </div>
        <div className="a-table-wrap">
          <table className="a-table">
            <thead>
              <tr>
                <th />
                <th>Vaqt</th>
                <th>Harakat</th>
                <th>Obyekt</th>
                <th className="num">Ball</th>
              </tr>
            </thead>
            <tbody>
              {user.activity.map((a) => {
                const voided = a.action === "voided";
                return (
                  <tr key={a.id} className={voided ? "is-voided" : undefined}>
                    <td>
                      {!voided && (
                        <input type="checkbox" aria-label="Tanlash" checked={selected.has(a.id)} onChange={() => toggle(a.id)} />
                      )}
                    </td>
                    <td className="a-small">{fmtDateTime(a.created_at)}</td>
                    <td>
                      {ACTION_LABEL[voided ? String(a.voided?.action) : a.action] ?? a.action}
                      {voided && (
                        <span className="a-pill a-pill--danger" style={{ marginLeft: 6, textDecoration: "none" }}>
                          bekor qilingan: {String(a.voided?.reason ?? "")}
                        </span>
                      )}
                    </td>
                    <td className="a-mono">{a.object_id ?? "—"}</td>
                    <td className="num">{voided ? `${a.voided?.points ?? 0} → 0` : a.points}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          {user.activity.length === 0 && <p className="a-empty">Faoliyat yo'q.</p>}
        </div>
      </section>

      {dialog === "block" && (
        <ConfirmModal title="Foydalanuvchini bloklash" text="Ilovani ocholmaydi va reytingdan darhol chiqadi." confirm="Bloklash" danger reason onClose={() => setDialog(null)}
          onConfirm={async (reason) => apply(await adminApi.block(user.id, true, reason), "Bloklandi")} />
      )}
      {dialog === "unblock" && (
        <ConfirmModal title="Blokdan chiqarish" confirm="Blokdan chiqarish" reason onClose={() => setDialog(null)}
          onConfirm={async (reason) => apply(await adminApi.block(user.id, false, reason), "Blokdan chiqarildi")} />
      )}
      {dialog === "hide" && (
        <ConfirmModal title="Taxallusni yashirish" text="Foydalanuvchi reytingda ko'rinmaydi, ilovadan foydalanishda davom etadi." confirm="Yashirish" reason onClose={() => setDialog(null)}
          onConfirm={async (reason) => apply(await adminApi.nickname(user.id, "hide", reason), "Taxallus yashirildi")} />
      )}
      {dialog === "show" && (
        <ConfirmModal title="Taxallusni ko'rsatish" confirm="Ko'rsatish" reason onClose={() => setDialog(null)}
          onConfirm={async (reason) => apply(await adminApi.nickname(user.id, "show", reason), "Taxallus reytingga qaytdi")} />
      )}
      {dialog === "reset" && (
        <ConfirmModal title="Taxallusni majburiy o'zgartirish" text="Joriy taxallus o'chiriladi. Keyingi kirishda foydalanuvchi yangi taxallus tanlaydi." confirm="O'zgartirishni talab qilish" danger reason onClose={() => setDialog(null)}
          onConfirm={async (reason) => apply(await adminApi.nickname(user.id, "reset", reason), "Taxallus o'chirildi")} />
      )}
      {dialog === "void" && (
        <ConfirmModal
          title="Ballarni bekor qilish"
          text={`${selected.size} ta yozuvning ballari 0 ga tushadi. Jami ball, streak va bog'liq nishonlar qayta hisoblanadi; yozuvlar jurnalda qoladi.`}
          confirm="Bekor qilish"
          danger
          reason
          reasonRequired
          onClose={() => setDialog(null)}
          onConfirm={async (reason) => apply(await adminApi.voidPoints(user.id, [...selected], reason!), "Ballar bekor qilindi")}
        />
      )}
    </>
  );
}
