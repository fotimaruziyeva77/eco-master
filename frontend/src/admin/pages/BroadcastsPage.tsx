import { Send } from "lucide-react";
import { useEffect, useState } from "react";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, type Broadcast, type BroadcastAudience } from "../api";
import { ConfirmModal, fmtDateTime, LoadError, Loading, PageHead, percent, useToast } from "../ui";

const MAX_TEXT = 1000;

const AUDIENCE_LABEL: Record<BroadcastAudience, string> = {
  all: "Hammaga",
  student: "O'quvchilarga",
  teacher: "O'qituvchilarga",
  general: "Ota-onalarga",
};

const STATUS: Record<Broadcast["status"], [string, string]> = {
  queued: ["Navbatda", "a-pill--review"],
  sending: ["Yuborilmoqda", "a-pill--warn"],
  done: ["Yuborildi", "a-pill--ok"],
  cancelled: ["Bekor qilindi", "a-pill--draft"],
};

const LANGUAGES = [
  ["uz", "O'zbekcha"],
  ["ru", "Ruscha"],
  ["en", "Inglizcha"],
] as const;

type Texts = Record<(typeof LANGUAGES)[number][0], string>;

/** A message from the team to users through the bot (stage 7). */
export function BroadcastsPage() {
  const toast = useToast();
  const [audience, setAudience] = useState<BroadcastAudience>("all");
  const [texts, setTexts] = useState<Texts>({ uz: "", ru: "", en: "" });
  const [confirming, setConfirming] = useState(false);
  const list = useLoad(() => adminApi.broadcasts(), []);
  const size = useLoad(() => adminApi.broadcastAudience(audience), [audience]);

  // While something is going out, follow its progress.
  const busy = list.data?.items.some((b) => b.status === "queued" || b.status === "sending");
  useEffect(() => {
    if (!busy) return;
    const timer = window.setInterval(list.reload, 5000);
    return () => window.clearInterval(timer);
  }, [busy, list.reload]);

  const limitReached = list.data ? list.data.sent_this_week >= list.data.weekly_limit : false;
  // Only a count for the audience now picked: never the previous one while it reloads.
  const count = size.data?.audience === audience && size.error === undefined ? size.data.count : null;
  const nobody = count === 0;
  const ready = texts.uz.trim().length > 0 && !limitReached && count !== null && count > 0;

  return (
    <>
      <PageHead title="Xabar yuborish" />
      <p className="a-help" style={{ marginBottom: 12 }}>
        Bot orqali xabar. Faqat eslatmalarni yoqib qo'yganlar oladi. 7 kunda ko'pi bilan{" "}
        {list.data?.weekly_limit ?? 2} ta xabar — bolalarni charchatmaslik uchun.
        {list.data && ` Bu hafta: ${list.data.sent_this_week}.`}
      </p>

      <div className="a-grid-2">
        <section className="a-card">
          <label className="a-field">
            <span className="a-label">Kimga</span>
            <select
              className="a-select"
              value={audience}
              onChange={(e) => setAudience(e.target.value as BroadcastAudience)}
            >
              {Object.entries(AUDIENCE_LABEL).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
            <span className="a-help">
              {count !== null && `${count} kishi oladi`}
              {count === null && size.error === undefined && "…"}
              {size.error !== undefined && (
                <>
                  Sonini bilib bo'lmadi.{" "}
                  <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={size.reload}>
                    Qayta urinish
                  </button>
                </>
              )}
            </span>
          </label>
          {LANGUAGES.map(([lang, label]) => (
            <label key={lang} className="a-field">
              <span className="a-label">
                {label} {lang === "uz" ? <span className="a-req">*</span> : <span className="a-muted a-small">(ixtiyoriy)</span>}
              </span>
              <textarea
                className="a-textarea"
                value={texts[lang]}
                maxLength={MAX_TEXT}
                onChange={(e) => setTexts({ ...texts, [lang]: e.target.value })}
              />
              <span className="a-help">
                {texts[lang].length}/{MAX_TEXT}
                {lang !== "uz" && " · bo'sh qolsa, o'zbekcha matn yuboriladi"}
              </span>
            </label>
          ))}
          {limitReached && <p className="a-error">Bu hafta ruxsat etilgan xabarlar yuborib bo'lingan.</p>}
          {nobody && <p className="a-error">Bu guruhda eslatmalarni yoqqan foydalanuvchi yo'q.</p>}
          <button type="button" className="a-btn" disabled={!ready} onClick={() => setConfirming(true)}>
            <Send size={16} /> Yuborish
          </button>
        </section>

        <section className="a-card">
          <h2>Ko'rinishi</h2>
          <p className="a-help" style={{ marginBottom: 10 }}>
            Matn o'zgarishsiz, oddiy matn sifatida boradi; ostida «Ilovani ochish» tugmasi.
          </p>
          <div className="a-tg-preview">
            <div className="a-tg-bubble">{texts.uz.trim() || "Xabar matni"}</div>
            <div className="a-tg-button">Ilovani ochish</div>
          </div>
        </section>
      </div>

      <section className="a-card" style={{ marginTop: 16 }}>
        <h2>Yuborilganlar</h2>
        {list.loading && !list.data && <Loading />}
        {list.error !== undefined && !list.data && <LoadError error={list.error} onRetry={list.reload} />}
        {list.data && list.data.items.length === 0 && <p className="a-empty">Hali xabar yuborilmagan.</p>}
        {list.data && list.data.items.length > 0 && (
          <div className="a-table-wrap">
            <table className="a-table">
              <thead>
                <tr>
                  <th>Sana</th>
                  <th>Kimga</th>
                  <th>Matn</th>
                  <th>Holat</th>
                  <th className="num">Yetkazildi</th>
                  <th className="num">Ilovani ochdi</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {list.data.items.map((b) => (
                  <BroadcastRow key={b.id} broadcast={b} onChange={list.reload} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {confirming && (
        <ConfirmModal
          title="Xabar yuborilsinmi?"
          text={`${count} kishiga (${AUDIENCE_LABEL[audience].toLowerCase()}) yuboriladi. Buni qaytarib bo'lmaydi.`}
          confirm="Yuborish"
          onClose={() => setConfirming(false)}
          onConfirm={async () => {
            const text = Object.fromEntries(Object.entries(texts).filter(([, value]) => value.trim()));
            try {
              await adminApi.createBroadcast({ text, audience });
            } catch (failure) {
              // The server may have queued it and only the answer got lost: show the list as it is.
              list.reload();
              throw failure;
            }
            toast("Navbatga qo'yildi");
            setTexts({ uz: "", ru: "", en: "" });
            list.reload();
          }}
        />
      )}
    </>
  );
}

function BroadcastRow({ broadcast: b, onChange }: { broadcast: Broadcast; onChange: () => void }) {
  const toast = useToast();
  const [cancelling, setCancelling] = useState(false);
  const [label, pill] = STATUS[b.status];
  const delivered = b.total ? `${b.sent}/${b.total}` : String(b.sent);
  return (
    <tr>
      <td className="a-small">
        {fmtDateTime(b.created_at)}
        {b.created_by && <div className="a-muted">{b.created_by}</div>}
      </td>
      <td>{AUDIENCE_LABEL[b.audience]}</td>
      <td className="a-small" style={{ maxWidth: 320 }}>
        {b.text.uz.length > 120 ? `${b.text.uz.slice(0, 120)}…` : b.text.uz}
      </td>
      <td>
        <span className={`a-pill ${pill}`}>{label}</span>
      </td>
      <td className="num">
        {delivered}
        {b.failed > 0 && <div className="a-muted a-small">{b.failed} ta yetmadi</div>}
      </td>
      <td className="num">
        {b.opened}
        {b.sent > 0 && <div className="a-muted a-small">{percent(b.opened / b.sent)}</div>}
      </td>
      <td>
        {(b.status === "queued" || b.status === "sending") && (
          <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => setCancelling(true)}>
            To'xtatish
          </button>
        )}
        {cancelling && (
          <ConfirmModal
            title="Yuborish to'xtatilsinmi?"
            text="Hali olmaganlarga xabar bormaydi."
            confirm="To'xtatish"
            danger
            onClose={() => setCancelling(false)}
            onConfirm={async () => {
              await adminApi.cancelBroadcast(b.id);
              toast("To'xtatildi");
              onChange();
            }}
          />
        )}
      </td>
    </tr>
  );
}
