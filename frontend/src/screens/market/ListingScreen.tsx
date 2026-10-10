import { Flag, Hand, Heart, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate, useParams } from "react-router";

import { api, type Listing, type ReportReason } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Avatar, SubpageHeader } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { haptic } from "../../telegram";
import { CodeBox, marketError, PointCard, SafetyNote, StatusChip, useCategoryLabel, useShortDate } from "./parts";

const EDITABLE = new Set(["pending", "rejected", "approved", "hidden"]);
const OPEN_REQUEST = new Set(["pending", "accepted", "at_point"]);
const REPORT_REASONS: ReportReason[] = ["personal_info", "rude", "forbidden", "other"];

export function ListingScreen() {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const navigate = useNavigate();
  const back = useBack("/market");
  const data = useLoad(() => api.listing(Number(id)), [id]);
  const categories = useLoad(() => api.categories(), []);
  const label = useCategoryLabel(categories.data);
  const [override, setOverride] = useState<Listing | null>(null);
  const [busy, setBusy] = useState(false);
  const location = useLocation();
  // Just created or changed: say that it went to a moderator.
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(
    (location.state as { sent?: boolean } | null)?.sent ? { kind: "ok", text: t("market.form.sent") } : null,
  );
  const [sheet, setSheet] = useState<"report" | "delete" | null>(null);
  const listing = override?.id === Number(id) ? override : data.data;
  const canWithdraw = Boolean(listing?.my_request && OPEN_REQUEST.has(listing.my_request));

  async function run(action: () => Promise<Listing | void>, ok?: string) {
    if (busy) return;
    setBusy(true);
    setMessage(null);
    try {
      const result = await action();
      if (result) setOverride(result);
      haptic.success();
      if (ok) setMessage({ kind: "ok", text: ok });
    } catch (error) {
      haptic.error();
      setMessage({ kind: "error", text: marketError(t, error) });
    } finally {
      setBusy(false);
    }
  }

  async function toggleLike(item: Listing) {
    const result = await (item.liked ? api.unlike(item.id) : api.like(item.id));
    setOverride({ ...item, likes: result.likes, liked: result.liked });
  }

  return (
    <main className="screen screen--with-action">
      <SubpageHeader onBack={back} title={t("market.title")} />
      {data.loading && !listing && <InlineLoading />}
      {data.error !== undefined && !listing && <InlineError error={data.error} onRetry={data.reload} />}
      {listing && (
        <article className="stack stack--lg">
          <Photos listing={listing} />
          <div className="stack">
            <div className="chips">
              {listing.is_mine && <StatusChip status={listing.status} />}
              <span className="chip chip--sm chip--neutral">{t(`market.kind.${listing.kind}`)}</span>
              <span className="chip chip--sm chip--neutral">{label(listing.kind, listing.category)}</span>
              {listing.condition && (
                <span className="chip chip--sm chip--neutral">{t(`market.condition.${listing.condition}`)}</span>
              )}
              {listing.ready_at_point && <span className="chip chip--sm chip--sky">{t("market.readyAtPoint")}</span>}
            </div>
            <h1>{listing.title}</h1>
            {listing.description && <p className="text-2 pre-line">{listing.description}</p>}
            <div className="row">
              {listing.owner_id !== null && <Avatar id={listing.owner_id} />}
              <span className="hint">{t("market.by", { name: listing.owner_nickname ?? t("market.anonymous") })}</span>
            </div>
          </div>

          {listing.is_mine && <OwnerStatus listing={listing} />}
          <Handover listing={listing} busy={busy} onCancel={() => void run(() => api.cancelHandover(listing.id))} />
          {!listing.is_mine && listing.my_request && !listing.handover && (
            <p className="note">{t(`market.requestStatus.${listing.my_request}`)}</p>
          )}
          {listing.point && listing.giveaway && <PointCard point={listing.point} />}
          {listing.is_mine && <Requests listing={listing} busy={busy} run={run} />}

          <div className="row row--wrap">
            {!listing.is_mine && listing.status === "approved" && (
              <button
                type="button"
                className={listing.liked ? "btn btn--sm" : "btn btn--soft btn--sm"}
                aria-pressed={listing.liked}
                onClick={() => void toggleLike(listing)}
              >
                <Heart size={16} aria-hidden="true" fill={listing.liked ? "currentColor" : "none"} />
                {t("market.like")} · {listing.likes}
              </button>
            )}
            {listing.is_mine && EDITABLE.has(listing.status) && (
              <button type="button" className="btn btn--soft btn--sm" onClick={() => navigate(`/market/${listing.id}/edit`)}>
                <Pencil size={16} aria-hidden="true" /> {t("market.edit")}
              </button>
            )}
            {listing.is_mine && (EDITABLE.has(listing.status) || listing.status === "given") && !listing.ready_at_point && (
              <button type="button" className="btn btn--soft btn--sm" onClick={() => setSheet("delete")}>
                <Trash2 size={16} aria-hidden="true" /> {t("market.delete")}
              </button>
            )}
            {!listing.is_mine && listing.status === "approved" && (
              <button type="button" className="link-button" onClick={() => setSheet("report")}>
                <Flag size={14} aria-hidden="true" /> {t("market.report")}
              </button>
            )}
          </div>
        </article>
      )}

      {listing && (message || listing.can_request || canWithdraw) && (
        <div className="action-bar">
          {message && (
            <p className={message.kind === "ok" ? "toast" : "toast toast--error"} role="status">
              {message.text}
            </p>
          )}
          {listing.can_request && (
            <button
              type="button"
              className="btn btn--block"
              disabled={busy}
              onClick={() => void run(() => api.askFor(listing.id), t("market.requestSent"))}
            >
              <Hand size={20} aria-hidden="true" /> {t("market.requestCta")}
            </button>
          )}
          {canWithdraw && (
            <button
              type="button"
              className="btn btn--soft btn--block"
              disabled={busy}
              onClick={() => void run(() => api.withdrawRequest(listing.id))}
            >
              {t("market.requestWithdraw")}
            </button>
          )}
        </div>
      )}

      {sheet === "report" && listing && (
        <ReportSheet
          onClose={() => setSheet(null)}
          onReport={(reason) =>
            run(async () => {
              await api.reportListing(listing.id, reason);
              setSheet(null);
            }, t("market.reported"))
          }
        />
      )}
      {sheet === "delete" && listing && (
        <div className="overlay" role="dialog" aria-modal="true" onClick={() => setSheet(null)}>
          <div className="sheet stack" onClick={(e) => e.stopPropagation()}>
            <h2>{t("market.delete")}</h2>
            <p className="text-2">{t("market.deleteText")}</p>
            <button
              type="button"
              className="btn btn--block btn--danger"
              disabled={busy}
              onClick={() =>
                void run(async () => {
                  await api.deleteListing(listing.id);
                  navigate("/market/mine", { replace: true });
                })
              }
            >
              <Trash2 size={18} aria-hidden="true" /> {t("market.delete")}
            </button>
            <button type="button" className="link-button" onClick={() => setSheet(null)}>
              {t("common.cancel")}
            </button>
          </div>
        </div>
      )}
    </main>
  );
}

function Photos({ listing }: { listing: Listing }) {
  if (listing.photos.length === 0) return null;
  return (
    <div className="photo-strip" role="list">
      {listing.photos.map((photo) => (
        <img
          key={photo.id}
          role="listitem"
          src={photo.url}
          width={photo.width}
          height={photo.height}
          alt={listing.title}
          loading="lazy"
        />
      ))}
    </div>
  );
}

function OwnerStatus({ listing }: { listing: Listing }) {
  const { t } = useTranslation();
  if (!["pending", "rejected", "hidden"].includes(listing.status)) return null;
  const reason = listing.reject_reason ? t(`market.reason.${listing.reject_reason}`) : "";
  return (
    <section className={listing.status === "pending" ? "note" : "note note--danger"} role="status">
      <p>{t(`market.statusText.${listing.status}`, { reason })}</p>
      {listing.moderator_note && <p className="small">{t("market.moderatorNote", { note: listing.moderator_note })}</p>}
    </section>
  );
}

function Handover({ listing, busy, onCancel }: { listing: Listing; busy: boolean; onCancel: () => void }) {
  const { t } = useTranslation();
  const date = useShortDate();
  const handover = listing.handover;
  if (!handover) return null;
  const deadline = date(handover.deadline);
  const name = handover.other_nickname ?? t("market.anonymous");

  let body;
  if (listing.is_mine && handover.status === "accepted") {
    body = (
      <>
        <h3>{t("market.handover.bringTitle")}</h3>
        <p className="text-2">{t("market.handover.bringText", { date: deadline })}</p>
        {handover.code && <CodeBox code={handover.code} />}
        <p className="hint small">{t("market.handover.for", { name })}</p>
        <button type="button" className="btn btn--soft btn--sm" disabled={busy} onClick={onCancel}>
          {t("market.handover.cancel")}
        </button>
      </>
    );
  } else if (listing.is_mine) {
    body = (
      <>
        <p className="text-2">{t("market.handover.atPointOwner")}</p>
        <p className="hint small">{t("market.handover.for", { name })}</p>
      </>
    );
  } else if (handover.status === "accepted") {
    body = (
      <>
        <h3>{t("market.handover.waitTitle")}</h3>
        <p className="text-2">{t("market.handover.waitText")}</p>
      </>
    );
  } else {
    body = (
      <>
        <h3>{t("market.handover.pickTitle")}</h3>
        <p className="text-2">{t("market.handover.pickText", { date: deadline })}</p>
        {handover.code && <CodeBox code={handover.code} />}
      </>
    );
  }
  return (
    <section className="card card--soft stack handover">
      {body}
      <SafetyNote />
    </section>
  );
}

function Requests({
  listing,
  busy,
  run,
}: {
  listing: Listing;
  busy: boolean;
  run: (action: () => Promise<Listing | void>, ok?: string) => Promise<void>;
}) {
  const { t } = useTranslation();
  if (!listing.giveaway || listing.status !== "approved") return null;
  return (
    <section className="stack">
      <h3>{t("market.requests")}</h3>
      {listing.requests.length === 0 && <p className="hint">{t("market.noRequests")}</p>}
      {listing.requests.map((request) => (
        <div key={request.id} className="list-row">
          <Avatar id={request.requester_id} />
          <span className="list-row__text">
            <strong>{request.nickname ?? t("market.anonymous")}</strong>
          </span>
          <button
            type="button"
            className="btn btn--sm"
            disabled={busy}
            onClick={() => void run(() => api.acceptRequest(request.id))}
          >
            {t("market.accept")}
          </button>
          <button
            type="button"
            className="btn btn--soft btn--sm"
            disabled={busy}
            onClick={() => void run(() => api.declineRequest(request.id))}
          >
            {t("market.decline")}
          </button>
        </div>
      ))}
    </section>
  );
}

function ReportSheet({ onClose, onReport }: { onClose: () => void; onReport: (reason: ReportReason) => void }) {
  const { t } = useTranslation();
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label={t("market.reportTitle")} onClick={onClose}>
      <div className="sheet stack" onClick={(e) => e.stopPropagation()}>
        <h2>{t("market.reportTitle")}</h2>
        {REPORT_REASONS.map((reason) => (
          <button key={reason} type="button" className="list-row" onClick={() => onReport(reason)}>
            <span className="list-row__text">
              <strong>{t(`market.reportReason.${reason}`)}</strong>
            </span>
          </button>
        ))}
        <button type="button" className="link-button" onClick={onClose}>
          {t("common.cancel")}
        </button>
      </div>
    </div>
  );
}
