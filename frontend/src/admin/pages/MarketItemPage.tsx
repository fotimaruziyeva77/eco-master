import { ArrowLeft } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, errorText, type MarketListing, type MarketReason } from "../api";
import { ConfirmModal, fmtDateTime, LoadError, Loading, Modal, PageHead, useAdmin, useToast } from "../ui";
import { KIND_LABEL, REASONS, StatusBadge } from "./MarketPage";

const REQUEST_STATUS: Record<string, string> = {
  pending: "javob kutmoqda",
  accepted: "egasi rozi — olib kelinishi kutilmoqda",
  at_point: "topshirish joyida",
  done: "berildi",
  declined: "rad etildi",
  cancelled: "bekor qilindi",
  expired: "muddati o'tdi",
};

const REPORT_REASON: Record<string, string> = {
  personal_info: "Shaxsiy ma'lumot",
  rude: "Haqoratli",
  forbidden: "Taqiqlangan narsa",
  other: "Boshqa",
};

const CONDITION: Record<string, string> = { new: "Yangi", good: "Yaxshi holatda", used: "Ishlatilgan" };

/** One listing: photos, text and the moderator's decision. */
export function MarketItemPage() {
  const { id = "" } = useParams();
  const { me } = useAdmin();
  const toast = useToast();
  const navigate = useNavigate();
  const data = useLoad(() => adminApi.marketItem(Number(id)), [id]);
  const [item, setItem] = useState<MarketListing | null>(null);
  const [decision, setDecision] = useState<"reject" | "hide" | null>(null);
  const [confirm, setConfirm] = useState<"approve" | "dismiss" | null>(null);
  const listing = item?.id === Number(id) ? item : data.data;

  return (
    <>
      <PageHead title={listing ? listing.title : "E'lon"}>
        <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => navigate("/market")}>
          <ArrowLeft size={16} aria-hidden="true" /> Ro'yxatga
        </button>
      </PageHead>
      {data.loading && !listing && <Loading />}
      {data.error !== undefined && !listing && <LoadError error={data.error} onRetry={data.reload} />}
      {listing && (
        <div className="a-grid-2">
          <section className="a-card a-stack">
            <div className="a-market-photos">
              {listing.photos.map((photo) => (
                <a key={photo.id} href={photo.url} target="_blank" rel="noreferrer">
                  <img src={photo.url} alt="" width={photo.width} height={photo.height} />
                </a>
              ))}
            </div>
            <p className="a-help">Rasmlar serverda qayta saqlangan: joylashuv va kamera ma'lumotlari olib tashlangan.</p>
          </section>

          <div className="a-stack">
            <section className="a-card a-stack">
              <div className="a-row">
                <StatusBadge status={listing.status} />
                {listing.reports_open > 0 && <span className="a-pill a-pill--danger">{listing.reports_open} ochiq shikoyat</span>}
                {listing.stored_at_point && <span className="a-pill a-pill--warn">topshirish joyida saqlanmoqda</span>}
              </div>
              <h2 style={{ margin: 0 }}>{listing.title}</h2>
              {listing.description && <p style={{ whiteSpace: "pre-line", margin: 0 }}>{listing.description}</p>}
              <dl className="a-dl">
                <dt>Turi</dt>
                <dd>{KIND_LABEL[listing.kind]}</dd>
                <dt>Toifa</dt>
                <dd>{listing.category_name}</dd>
                {listing.condition && (
                  <>
                    <dt>Holati</dt>
                    <dd>{CONDITION[listing.condition] ?? listing.condition}</dd>
                  </>
                )}
                <dt>Beriladimi</dt>
                <dd>{listing.giveaway ? `Ha — ${listing.point_name ?? "?"}` : "Yo'q, faqat ko'rgazma"}</dd>
                <dt>Muallif</dt>
                <dd>
                  {listing.owner_id === null
                    ? "hisob o'chirilgan"
                    : me.role === "admin"
                      ? <Link to={`/users/${listing.owner_id}`}>@{listing.owner_nickname ?? listing.owner_id}</Link>
                      : `@${listing.owner_nickname ?? listing.owner_id}`}
                </dd>
                <dt>Yuborilgan</dt>
                <dd>{fmtDateTime(listing.submitted_at)}</dd>
                <dt>«Zo'r!»</dt>
                <dd>{listing.likes}</dd>
                {listing.reviewed_at && (
                  <>
                    <dt>Ko'rib chiqdi</dt>
                    <dd>
                      {listing.reviewed_by ?? "—"}, {fmtDateTime(listing.reviewed_at)}
                    </dd>
                  </>
                )}
                {listing.reject_reason && (
                  <>
                    <dt>Sabab</dt>
                    <dd>
                      {REASONS.find(([value]) => value === listing.reject_reason)?.[1] ?? listing.reject_reason}
                      {listing.moderator_note && <div className="a-small a-muted">«{listing.moderator_note}»</div>}
                    </dd>
                  </>
                )}
              </dl>
              <div className="a-row">
                {(listing.status === "pending" || listing.status === "hidden") && (
                  <button type="button" className="a-btn" onClick={() => setConfirm("approve")}>
                    {listing.status === "pending" ? "Tasdiqlash" : "Bozorga qaytarish"}
                  </button>
                )}
                {listing.status === "pending" && (
                  <button type="button" className="a-btn a-btn--amber" onClick={() => setDecision("reject")}>
                    Qaytarish
                  </button>
                )}
                {["approved", "reserved", "at_point"].includes(listing.status) && (
                  <button type="button" className="a-btn a-btn--danger" onClick={() => setDecision("hide")}>
                    Bozordan olib tashlash
                  </button>
                )}
                {listing.reports_open > 0 && (
                  <button type="button" className="a-btn a-btn--ghost" onClick={() => setConfirm("dismiss")}>
                    Shikoyatlar asossiz
                  </button>
                )}
              </div>
            </section>

            {listing.reports.length > 0 && (
              <section className="a-card">
                <h3>Shikoyatlar</h3>
                <ul className="a-list">
                  {listing.reports.map((r) => (
                    <li key={r.id} className="a-list-row">
                      <span>{REPORT_REASON[r.reason] ?? r.reason}</span>
                      <span className="a-small a-muted">
                        {fmtDateTime(r.created_at)} · {r.status === "open" ? "ochiq" : r.status === "resolved" ? "hal qilingan" : "rad etilgan"}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {listing.requests.length > 0 && (
              <section className="a-card">
                <h3>So'rovlar</h3>
                <ul className="a-list">
                  {listing.requests.map((r) => (
                    <li key={r.id} className="a-list-row">
                      <span>@{r.nickname ?? r.requester_id}</span>
                      <span className="a-small a-muted">
                        {REQUEST_STATUS[r.status] ?? r.status} · {fmtDateTime(r.given_at ?? r.dropped_at ?? r.decided_at ?? r.created_at)}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            )}
          </div>
        </div>
      )}

      {listing && confirm && (
        <ConfirmModal
          title={confirm === "approve" ? "Bozorga chiqarish" : "Shikoyatlarni yopish"}
          text={
            confirm === "approve"
              ? "E'lon hammaga ko'rinadi, muallifga bot orqali xabar boradi."
              : "Shikoyatlar asossiz deb yopiladi; e'lon o'zgarmaydi."
          }
          confirm={confirm === "approve" ? "Tasdiqlash" : "Yopish"}
          onClose={() => setConfirm(null)}
          onConfirm={async () => {
            const next =
              confirm === "approve" ? await adminApi.approveListing(listing.id) : await adminApi.dismissReports(listing.id);
            setItem(next);
            toast("Saqlandi");
          }}
        />
      )}
      {listing && decision && (
        <DecisionModal
          kind={decision}
          onClose={() => setDecision(null)}
          onSubmit={async (reason, note) => {
            const body = { reason, note };
            const next =
              decision === "reject"
                ? await adminApi.rejectListing(listing.id, body)
                : await adminApi.hideListing(listing.id, body);
            setItem(next);
            toast("Saqlandi");
          }}
        />
      )}
    </>
  );
}

function DecisionModal({
  kind,
  onClose,
  onSubmit,
}: {
  kind: "reject" | "hide";
  onClose: () => void;
  onSubmit: (reason: MarketReason, note: string | null) => Promise<void>;
}) {
  const [reason, setReason] = useState<MarketReason>("personal_info");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await onSubmit(reason, note.trim() || null);
      onClose();
    } catch (e) {
      setError(errorText(e));
      setBusy(false);
    }
  }

  return (
    <Modal title={kind === "reject" ? "E'lonni qaytarish" : "Bozordan olib tashlash"} onClose={onClose}>
      <p className="a-muted">
        {kind === "reject"
          ? "Bola sababni bot orqali o'z tilida oladi va e'lonni tuzatib qayta yuborishi mumkin."
          : "E'lon bozordan yo'qoladi; boshlangan topshirish bekor qilinadi. Bola sababni bot orqali oladi."}
      </p>
      <label className="a-field" style={{ margin: 0 }}>
        <span className="a-label">Sabab</span>
        <select className="a-select" value={reason} onChange={(e) => setReason(e.target.value as MarketReason)}>
          {REASONS.map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label className="a-field" style={{ margin: 0 }}>
        <span className="a-label">
          Izoh bolaga <span className="a-muted a-small">(ixtiyoriy)</span>
        </span>
        <textarea className="a-textarea" value={note} maxLength={300} rows={3} onChange={(e) => setNote(e.target.value)} />
        <span className="a-help">Qisqa va mehribon yozing, masalan: «Buyumni yuzingiz ko'rinmaydigan qilib suratga oling».</span>
      </label>
      {error && <p className="a-error">{error}</p>}
      <div className="a-row" style={{ justifyContent: "flex-end" }}>
        <button type="button" className="a-btn a-btn--ghost" onClick={onClose}>
          Bekor qilish
        </button>
        <button type="button" className={kind === "hide" ? "a-btn a-btn--danger" : "a-btn a-btn--amber"} disabled={busy} onClick={() => void submit()}>
          {kind === "reject" ? "Qaytarish" : "Olib tashlash"}
        </button>
      </div>
    </Modal>
  );
}
