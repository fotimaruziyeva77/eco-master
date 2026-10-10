import { useState, type FormEvent } from "react";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, errorText, type AdminRole, type AdminRow, type HandoverPoint } from "../api";
import { ConfirmModal, fmtDateTime, LoadError, Loading, Modal, PageHead, ROLE_LABEL, useAdmin, useToast } from "../ui";

/** Admin and content editor accounts (TZ 8.12 roles). */
export function AdminsPage() {
  const { me } = useAdmin();
  const toast = useToast();
  const admins = useLoad(() => adminApi.admins(), []);
  const points = useLoad(() => adminApi.handoverPoints(), []);
  const pointName = (id: number | null | undefined) => points.data?.find((p) => p.id === id)?.name ?? "?";
  const [creating, setCreating] = useState(false);
  const [passwordFor, setPasswordFor] = useState<AdminRow | null>(null);
  const [resetFor, setResetFor] = useState<AdminRow | null>(null);

  async function update(
    row: AdminRow,
    body: { role?: AdminRole; is_active?: boolean; pickup_point_id?: number | null },
  ) {
    try {
      await adminApi.updateAdmin(row.id, body);
      toast("Saqlandi");
      admins.reload();
    } catch (e) {
      toast(errorText(e));
    }
  }

  return (
    <>
      <PageHead title="Adminlar">
        <button type="button" className="a-btn" onClick={() => setCreating(true)}>
          Yangi admin
        </button>
      </PageHead>
      <p className="a-help" style={{ marginBottom: 14 }}>
        Administrator hamma bo'limlarni boshqaradi; kontent muharriri kontent, jadval va bozor e'lonlari bilan
        ishlaydi; topshirish joyi xodimi faqat o'z joyining topshirish pultini ko'radi. Har bir kishi birinchi
        kirishda autentifikator ilovasini ulaydi.
      </p>
      {admins.loading && !admins.data && <Loading />}
      {admins.error !== undefined && !admins.data && <LoadError error={admins.error} onRetry={admins.reload} />}
      {admins.data && (
        <div className="a-table-wrap">
          <table className="a-table">
            <thead>
              <tr>
                <th>Login</th>
                <th>Ism</th>
                <th>Rol</th>
                <th>Holat</th>
                <th>Oxirgi kirish</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {admins.data.map((a) => {
                const self = a.id === me.id;
                return (
                  <tr key={a.id}>
                    <td className="a-mono">{a.login}</td>
                    <td>
                      {a.name} {self && <span className="a-pill a-pill--ok">siz</span>}
                    </td>
                    <td>
                      <select
                        className="a-select"
                        value={a.role}
                        disabled={self || a.role === "point"}
                        onChange={(e) => void update(a, { role: e.target.value as AdminRole })}
                      >
                        <option value="admin">{ROLE_LABEL.admin}</option>
                        <option value="editor">{ROLE_LABEL.editor}</option>
                        {a.role === "point" && <option value="point">{ROLE_LABEL.point}</option>}
                      </select>
                      {a.role === "point" && <div className="a-small a-muted">{pointName(a.pickup_point_id)}</div>}
                    </td>
                    <td>
                      <span className="a-row" style={{ gap: 4 }}>
                        {a.is_active ? <span className="a-pill a-pill--ok">faol</span> : <span className="a-pill a-pill--draft">o'chirilgan</span>}
                        {!a.totp_enabled && <span className="a-pill a-pill--warn">2FA ulanmagan</span>}
                        {a.locked && <span className="a-pill a-pill--danger">vaqtincha bloklangan</span>}
                      </span>
                    </td>
                    <td className="a-small a-muted">{fmtDateTime(a.last_login_at)}</td>
                    <td>
                      {!self && (
                        <span className="a-row" style={{ gap: 4, flexWrap: "nowrap" }}>
                          <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => void update(a, { is_active: !a.is_active })}>
                            {a.is_active ? "O'chirish" : "Faollashtirish"}
                          </button>
                          <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => setPasswordFor(a)}>
                            Parol
                          </button>
                          <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => setResetFor(a)}>
                            2FA ni tiklash
                          </button>
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {creating && (
        <CreateAdmin points={points.data ?? []} onClose={() => setCreating(false)} onCreated={() => admins.reload()} />
      )}
      {passwordFor && <SetPassword admin={passwordFor} onClose={() => setPasswordFor(null)} />}
      {resetFor && (
        <ConfirmModal
          title={`${resetFor.name}: 2FA ni tiklash`}
          text="Telefon yo'qolgan bo'lsa: keyingi kirishda yangi autentifikator ilovasi ulanadi. Joriy sessiyalar tugaydi."
          confirm="Tiklash"
          onClose={() => setResetFor(null)}
          onConfirm={async () => {
            await adminApi.reset2fa(resetFor.id);
            toast("2FA tiklandi");
            admins.reload();
          }}
        />
      )}
    </>
  );
}

function CreateAdmin({
  points,
  onClose,
  onCreated,
}: {
  points: HandoverPoint[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const toast = useToast();
  const [form, setForm] = useState({
    login: "",
    name: "",
    role: "editor" as AdminRole,
    password: "",
    pickup_point_id: null as number | null,
  });
  const [error, setError] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      await adminApi.createAdmin({ ...form, login: form.login.trim().toLowerCase() });
      toast("Admin qo'shildi");
      onCreated();
      onClose();
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <Modal title="Yangi admin" onClose={onClose}>
      <form className="a-stack" onSubmit={(e) => void submit(e)}>
        <label className="a-field" style={{ margin: 0 }}>
          <span className="a-label">Login</span>
          <input className="a-input" value={form.login} pattern="[a-z0-9._-]{3,64}" required autoComplete="off"
            onChange={(e) => setForm({ ...form, login: e.target.value })} />
          <span className="a-help">Kichik lotin harflari, raqamlar, «.», «_», «-».</span>
        </label>
        <label className="a-field" style={{ margin: 0 }}>
          <span className="a-label">Ism</span>
          <input className="a-input" value={form.name} required maxLength={64} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        </label>
        <label className="a-field" style={{ margin: 0 }}>
          <span className="a-label">Rol</span>
          <select className="a-select" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as AdminRole })}>
            <option value="editor">{ROLE_LABEL.editor}</option>
            <option value="admin">{ROLE_LABEL.admin}</option>
            <option value="point">{ROLE_LABEL.point}</option>
          </select>
        </label>
        {form.role === "point" && (
          <label className="a-field" style={{ margin: 0 }}>
            <span className="a-label">Topshirish joyi</span>
            <select
              className="a-select"
              value={form.pickup_point_id ?? ""}
              required
              onChange={(e) => setForm({ ...form, pickup_point_id: Number(e.target.value) || null })}
            >
              <option value="">—</option>
              {points.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <span className="a-help">Xodim faqat shu joyning topshirish pultini ko'radi.</span>
          </label>
        )}
        <label className="a-field" style={{ margin: 0 }}>
          <span className="a-label">Vaqtinchalik parol</span>
          <input className="a-input" type="password" value={form.password} minLength={10} required autoComplete="new-password"
            onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <span className="a-help">Kamida 10 belgi. Uni shaxsan yetkazing; kirgandan keyin o'zgartirish mumkin.</span>
        </label>
        {error && <p className="a-error">{error}</p>}
        <div className="a-row" style={{ justifyContent: "flex-end" }}>
          <button type="button" className="a-btn a-btn--ghost" onClick={onClose}>
            Bekor qilish
          </button>
          <button type="submit" className="a-btn">
            Qo'shish
          </button>
        </div>
      </form>
    </Modal>
  );
}

function SetPassword({ admin, onClose }: { admin: AdminRow; onClose: () => void }) {
  const toast = useToast();
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      await adminApi.setAdminPassword(admin.id, password);
      toast("Yangi parol o'rnatildi");
      onClose();
    } catch (err) {
      setError(errorText(err));
    }
  }
  return (
    <Modal title={`${admin.name}: vaqtinchalik parol`} onClose={onClose}>
      <form className="a-stack" onSubmit={(e) => void submit(e)}>
        <input className="a-input" type="password" value={password} minLength={10} required autoComplete="new-password" autoFocus
          onChange={(e) => setPassword(e.target.value)} />
        <span className="a-help">Bloklangan hisob ham ochiladi; joriy sessiyalar tugaydi.</span>
        {error && <p className="a-error">{error}</p>}
        <button type="submit" className="a-btn">
          O'rnatish
        </button>
      </form>
    </Modal>
  );
}
