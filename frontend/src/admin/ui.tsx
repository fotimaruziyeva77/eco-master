import { X } from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import type { AdminMe, ContentStatus } from "./api";
import { errorText } from "./api";

// ----------------------------------------------------------------- session

export const AdminContext = createContext<{ me: AdminMe; signOut: () => void } | null>(null);

export function useAdmin() {
  const value = useContext(AdminContext);
  if (!value) throw new Error("useAdmin outside AdminContext");
  return value;
}

// ------------------------------------------------------------------ toasts

const ToastContext = createContext<(text: string) => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [text, setText] = useState<string | null>(null);
  const timer = useRef<number>(0);
  const show = useCallback((value: string) => {
    window.clearTimeout(timer.current);
    setText(value);
    timer.current = window.setTimeout(() => setText(null), 3000);
  }, []);
  return (
    <ToastContext.Provider value={show}>
      {children}
      {text && (
        <div className="a-toast" role="status">
          {text}
        </div>
      )}
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);

// -------------------------------------------------------------- formatting

const TZ = "Asia/Tashkent";

function parts(value: string | Date, withTime: boolean): Record<string, string> {
  const format = new Intl.DateTimeFormat("en-GB", {
    timeZone: TZ,
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    ...(withTime ? { hour: "2-digit", minute: "2-digit", hourCycle: "h23" } : {}),
  });
  return Object.fromEntries(format.formatToParts(new Date(value)).map((p) => [p.type, p.value]));
}

/** 10.10.2026, Tashkent time. */
export function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  // A plain date ("2026-10-10") is already a Tashkent day.
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const [y, m, d] = value.split("-");
    return `${d}.${m}.${y}`;
  }
  const p = parts(value, false);
  return `${p.day}.${p.month}.${p.year}`;
}

/** 10.10.2026 18:05, Tashkent time. */
export function fmtDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const p = parts(value, true);
  return `${p.day}.${p.month}.${p.year} ${p.hour}:${p.minute}`;
}

export function percent(rate: number | null | undefined): string {
  return rate === null || rate === undefined ? "—" : `${Math.round(rate * 100)}%`;
}

export const ROLE_LABEL: Record<string, string> = {
  admin: "Administrator",
  editor: "Kontent muharriri",
  point: "Topshirish joyi xodimi",
};
export const PATH_LABEL: Record<string, string> = { student: "O'quvchi", teacher: "O'qituvchi", general: "Ota-ona" };

export const STATUS_LABEL: Record<ContentStatus, string> = {
  draft: "Qoralama",
  review: "Tekshiruvda",
  published: "Nashr qilingan",
  archived: "Arxiv",
};

export function StatusPill({ status }: { status: ContentStatus | null | undefined }) {
  if (!status) return null;
  return <span className={`a-pill a-pill--${status}`}>{STATUS_LABEL[status]}</span>;
}

// ---------------------------------------------------------------- building

export function PageHead({ title, children }: { title: string; children?: ReactNode }) {
  useEffect(() => {
    document.title = `${title} — Ekoustoz admin`;
  }, [title]);
  return (
    <div className="a-page-head">
      <h1>{title}</h1>
      {children}
    </div>
  );
}

export function Loading() {
  return (
    <div className="a-empty" aria-busy="true">
      <div className="spinner" style={{ margin: "0 auto 8px" }} />
      Yuklanmoqda…
    </div>
  );
}

export function LoadError({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div className="a-empty" role="alert">
      <p className="a-error">{errorText(error)}</p>
      {onRetry && (
        <button type="button" className="a-btn a-btn--ghost a-btn--sm" style={{ marginTop: 10 }} onClick={onRetry}>
          Qayta urinish
        </button>
      )}
    </div>
  );
}

export function Modal({
  title,
  onClose,
  children,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="a-backdrop" onMouseDown={onClose}>
      <div className="a-modal" role="dialog" aria-modal="true" aria-label={title} onMouseDown={(e) => e.stopPropagation()}>
        <div className="a-row">
          <h2 style={{ marginRight: "auto" }}>{title}</h2>
          <button type="button" className="a-icon-btn" onClick={onClose} aria-label="Yopish">
            <X size={16} />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

/** Asks for confirmation, optionally with a reason that goes to the audit log. */
export function ConfirmModal({
  title,
  text,
  confirm,
  danger,
  reason,
  reasonRequired,
  onConfirm,
  onClose,
}: {
  title: string;
  text?: ReactNode;
  confirm: string;
  danger?: boolean;
  reason?: boolean;
  reasonRequired?: boolean;
  onConfirm: (reason: string | null) => Promise<void>;
  onClose: () => void;
}) {
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const missing = reasonRequired && value.trim().length < 3;

  async function run() {
    setBusy(true);
    setError(null);
    try {
      await onConfirm(value.trim() || null);
      onClose();
    } catch (e) {
      setError(errorText(e));
      setBusy(false);
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      {text && <div className="a-muted">{text}</div>}
      {reason && (
        <label className="a-field" style={{ margin: 0 }}>
          <span className="a-label">
            Sabab {reasonRequired ? <span className="a-req">*</span> : <span className="a-muted a-small">(ixtiyoriy)</span>}
          </span>
          <input className="a-input" value={value} maxLength={200} autoFocus onChange={(e) => setValue(e.target.value)} />
          <span className="a-help">Audit jurnaliga yoziladi.</span>
        </label>
      )}
      {error && <p className="a-error">{error}</p>}
      <div className="a-row" style={{ justifyContent: "flex-end" }}>
        <button type="button" className="a-btn a-btn--ghost" onClick={onClose}>
          Bekor qilish
        </button>
        <button
          type="button"
          className={danger ? "a-btn a-btn--danger" : "a-btn"}
          disabled={busy || missing}
          onClick={() => void run()}
        >
          {confirm}
        </button>
      </div>
    </Modal>
  );
}
