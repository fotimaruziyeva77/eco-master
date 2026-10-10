import { PackageCheck, PackageOpen, Search } from "lucide-react";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, errorText, type HandoverItem, type HandoverMatch } from "../api";
import { ConfirmModal, fmtDate, LoadError, Loading, PageHead, useAdmin, useToast } from "../ui";

/**
 * The desk of a handover point. A child says a six-digit code: the owner's code when bringing
 * an item, the new owner's code when collecting it. Children never need to meet.
 */
export function HandoverPage() {
  const { me } = useAdmin();
  const toast = useToast();
  const points = useLoad(() => adminApi.handoverPoints(), []);
  const [pointId, setPointId] = useState<number | null>(me.role === "point" ? (me.pickup_point_id ?? null) : null);
  const desk = useLoad(
    () => (pointId === null ? Promise.resolve(null) : adminApi.handoverDesk(pointId)),
    [pointId],
  );
  const [code, setCode] = useState("");
  const [match, setMatch] = useState<HandoverMatch | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [returning, setReturning] = useState<HandoverItem | null>(null);

  useEffect(() => {
    // Administrators start with the first point.
    if (pointId === null && points.data?.length) setPointId(points.data[0].id);
  }, [points.data, pointId]);

  async function lookup(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setMatch(null);
    try {
      setMatch(await adminApi.handoverLookup(code, pointId));
    } catch (err) {
      setError(errorText(err));
    }
  }

  async function confirm() {
    if (!match?.item.request_id) return;
    setBusy(true);
    setError(null);
    try {
      if (match.action === "receive") await adminApi.handoverReceive(match.item.request_id, code);
      else await adminApi.handoverGive(match.item.request_id, code);
      toast(match.action === "receive" ? "Qabul qilindi. Oluvchiga xabar ketdi." : "Berildi. Rahmat!");
      setMatch(null);
      setCode("");
      desk.reload();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <PageHead title="Topshirish pulti">
        {me.role !== "point" && points.data && points.data.length > 0 && (
          <select className="a-select" value={pointId ?? ""} onChange={(e) => setPointId(Number(e.target.value))}>
            {points.data.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        )}
      </PageHead>
      {points.data?.length === 0 && (
        <p className="a-empty">Hali topshirish joyi yo'q. Uni «Kontent → Topshirish joylari» bo'limida qo'shing.</p>
      )}

      {pointId !== null && (
        <section className="a-card a-stack" style={{ marginBottom: 16 }}>
          <h2 style={{ margin: 0 }}>{desk.data?.point.name ?? ""}</h2>
          <p className="a-help">
            Bola aytgan 6 xonali kodni kiriting. Buyumni rasmdagi bilan solishtiring. Bolalarning ismi, telefoni yoki
            manzili so'ralmaydi.
          </p>
          <form className="a-row" onSubmit={(e) => void lookup(e)}>
            <input
              className="a-input a-code-input"
              inputMode="numeric"
              autoComplete="off"
              pattern="[0-9]{6}"
              maxLength={6}
              placeholder="000000"
              value={code}
              aria-label="Kod"
              onChange={(e) => {
                setCode(e.target.value.replace(/\D/g, ""));
                setMatch(null);
              }}
            />
            <button type="submit" className="a-btn" disabled={code.length !== 6}>
              <Search size={16} aria-hidden="true" /> Topish
            </button>
          </form>
          {error && <p className="a-error">{error}</p>}
          {match && (
            <div className="a-handover-match">
              {match.item.thumb_url && <img className="a-thumb a-thumb--lg" src={match.item.thumb_url} alt="" />}
              <div className="a-stack" style={{ gap: 4 }}>
                <strong>{match.item.title}</strong>
                <span className="a-small a-muted">
                  {match.action === "receive"
                    ? `Egasi olib keldi: @${match.item.owner_nickname ?? "—"}`
                    : `Oluvchi: @${match.item.requester_nickname ?? "—"}`}
                </span>
                <button type="button" className="a-btn" disabled={busy} onClick={() => void confirm()}>
                  {match.action === "receive" ? (
                    <>
                      <PackageOpen size={16} aria-hidden="true" /> Qabul qildim
                    </>
                  ) : (
                    <>
                      <PackageCheck size={16} aria-hidden="true" /> Berdim
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </section>
      )}

      {desk.loading && !desk.data && pointId !== null && <Loading />}
      {desk.error !== undefined && !desk.data && <LoadError error={desk.error} onRetry={desk.reload} />}
      {desk.data && (
        <div className="a-stack">
          <DeskList title="Olib kelinishi kutilmoqda" empty="Hech narsa kutilmayapti." items={desk.data.waiting_drop} />
          <DeskList title="Olib ketilishi kutilmoqda" empty="Topshirish joyida kutayotgan buyum yo'q." items={desk.data.waiting_pick} />
          <DeskList
            title="Egasiz turibdi (oluvchi kelmadi)"
            empty="Yo'q."
            items={desk.data.stored}
            action={(item) => (
              <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => setReturning(item)}>
                Egasiga qaytarildi
              </button>
            )}
          />
        </div>
      )}

      {returning && (
        <ConfirmModal
          title={`«${returning.title}»: egasiga qaytarildi`}
          text="Buyum egasiga qaytarib berilganini belgilaysiz. Egasining hisobi o'chirilgan bo'lsa, e'lon o'chiriladi."
          confirm="Belgilash"
          onClose={() => setReturning(null)}
          onConfirm={async () => {
            await adminApi.handoverReturn(returning.listing_id);
            toast("Belgilandi");
            desk.reload();
          }}
        />
      )}
    </>
  );
}

function DeskList({
  title,
  empty,
  items,
  action,
}: {
  title: string;
  empty: string;
  items: HandoverItem[];
  action?: (item: HandoverItem) => ReactNode;
}) {
  return (
    <section className="a-card">
      <h3>
        {title} <span className="a-muted">({items.length})</span>
      </h3>
      {items.length === 0 && <p className="a-muted a-small">{empty}</p>}
      <ul className="a-list">
        {items.map((item) => (
          <li key={`${item.listing_id}-${item.request_id ?? "s"}`} className="a-list-row">
            {item.thumb_url && <img className="a-thumb" src={item.thumb_url} alt="" loading="lazy" />}
            <span style={{ flex: 1 }}>
              <strong>{item.title}</strong>
              <div className="a-small a-muted">
                @{item.owner_nickname ?? "—"}
                {item.requester_nickname && ` → @${item.requester_nickname}`}
                {item.deadline && ` · muddat ${fmtDate(item.deadline)}`}
              </div>
            </span>
            {action?.(item)}
          </li>
        ))}
      </ul>
    </section>
  );
}
