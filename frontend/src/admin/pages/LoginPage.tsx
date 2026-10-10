import { useState, type FormEvent } from "react";

import { QrCode } from "../../components/QrCode";
import { adminApi, errorText, type AdminMe, type LoginResult } from "../api";

/** Login and password, then the authenticator code (TZ 8.12: 2FA for everyone). */
export function LoginPage({ onSignedIn }: { onSignedIn: (me: AdminMe) => void }) {
  const [login, setLogin] = useState("");
  const [password, setPassword] = useState("");
  const [step, setStep] = useState<LoginResult | null>(null);
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submitPassword(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      setStep(await adminApi.login(login, password));
      setPassword("");
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  async function submitCode(e: FormEvent) {
    e.preventDefault();
    if (!step) return;
    setBusy(true);
    setError(null);
    try {
      onSignedIn(await adminApi.code(step.token, code));
    } catch (err) {
      const text = errorText(err);
      setError(text);
      setCode("");
      // An expired step means starting again with the password.
      if (text.startsWith("Vaqt tugadi")) setStep(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="a-login">
      {step === null ? (
        <form className="a-card" onSubmit={(e) => void submitPassword(e)}>
          <div className="a-brand" style={{ padding: 0 }}>
            <span className="logo" aria-hidden="true">
              🌱
            </span>
            <span>
              Ekoustoz
              <small>Admin panel</small>
            </span>
          </div>
          <label className="a-field" style={{ margin: 0 }}>
            <span className="a-label">Login</span>
            <input
              className="a-input"
              value={login}
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              autoFocus
              onChange={(e) => setLogin(e.target.value)}
            />
          </label>
          <label className="a-field" style={{ margin: 0 }}>
            <span className="a-label">Parol</span>
            <input
              className="a-input"
              type="password"
              value={password}
              autoComplete="current-password"
              onChange={(e) => setPassword(e.target.value)}
            />
          </label>
          {error && (
            <p className="a-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="a-btn" disabled={busy || !login || !password}>
            Davom etish
          </button>
        </form>
      ) : (
        <form className="a-card" onSubmit={(e) => void submitCode(e)}>
          {step.setup ? (
            <>
              <h1 style={{ fontSize: 20 }}>Ikki bosqichli tasdiqlashni ulang</h1>
              <p className="a-muted a-small">
                Telefoningizdagi autentifikator ilovasida (Google Authenticator, Authy, 2FAS va h.k.) QR-kodni
                skanerlang, so'ng ilova ko'rsatgan 6 xonali kodni kiriting.
              </p>
              <QrCode value={step.setup.uri} label="Autentifikator uchun QR-kod" className="qr a-qr" />
              <p className="a-small">
                Skaner ishlamasa, kalitni qo'lda kiriting:{" "}
                <code className="a-mono" style={{ userSelect: "all", overflowWrap: "anywhere" }}>
                  {step.setup.secret}
                </code>
              </p>
            </>
          ) : (
            <>
              <h1 style={{ fontSize: 20 }}>Tasdiqlash kodi</h1>
              <p className="a-muted a-small">Autentifikator ilovasidagi 6 xonali kodni kiriting.</p>
            </>
          )}
          <input
            className="a-input a-code"
            value={code}
            inputMode="numeric"
            autoComplete="one-time-code"
            maxLength={6}
            autoFocus
            aria-label="6 xonali kod"
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          />
          {error && (
            <p className="a-error" role="alert">
              {error}
            </p>
          )}
          <button type="submit" className="a-btn" disabled={busy || code.length !== 6}>
            Kirish
          </button>
          <button type="button" className="a-btn a-btn--ghost" onClick={() => setStep(null)}>
            Orqaga
          </button>
        </form>
      )}
    </main>
  );
}
