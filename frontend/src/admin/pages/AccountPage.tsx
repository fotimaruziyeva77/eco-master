import { useState, type FormEvent } from "react";

import { adminApi, errorText } from "../api";
import { PageHead, ROLE_LABEL, useAdmin, useToast } from "../ui";

export function AccountPage() {
  const { me } = useAdmin();
  const toast = useToast();
  const [form, setForm] = useState({ current: "", next: "", repeat: "" });
  const [error, setError] = useState<string | null>(null);
  const mismatch = form.repeat !== "" && form.next !== form.repeat;

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await adminApi.changePassword(form.current, form.next);
      setForm({ current: "", next: "", repeat: "" });
      toast("Parol o'zgartirildi. Boshqa qurilmalardagi sessiyalar tugadi.");
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <>
      <PageHead title="Parolni o'zgartirish" />
      <form className="a-card a-stack" style={{ maxWidth: 440 }} onSubmit={(e) => void submit(e)}>
        <p className="a-muted a-small">
          {me.name} · {me.login} · {ROLE_LABEL[me.role]}
        </p>
        <label className="a-field" style={{ margin: 0 }}>
          <span className="a-label">Joriy parol</span>
          <input className="a-input" type="password" autoComplete="current-password" value={form.current}
            onChange={(e) => setForm({ ...form, current: e.target.value })} />
        </label>
        <label className="a-field" style={{ margin: 0 }}>
          <span className="a-label">Yangi parol</span>
          <input className="a-input" type="password" autoComplete="new-password" minLength={10} value={form.next}
            onChange={(e) => setForm({ ...form, next: e.target.value })} />
          <span className="a-help">Kamida 10 belgi.</span>
        </label>
        <label className="a-field" style={{ margin: 0 }}>
          <span className="a-label">Yangi parolni takrorlang</span>
          <input className={mismatch ? "a-input is-invalid" : "a-input"} type="password" autoComplete="new-password" value={form.repeat}
            onChange={(e) => setForm({ ...form, repeat: e.target.value })} />
          {mismatch && <span className="a-error">Parollar mos emas</span>}
        </label>
        {error && <p className="a-error">{error}</p>}
        <button type="submit" className="a-btn" disabled={!form.current || form.next.length < 10 || form.next !== form.repeat}>
          O'zgartirish
        </button>
      </form>
    </>
  );
}
