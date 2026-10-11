import { BookOpenCheck, ImagePlus, Send, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router";

import { api, type Listing, type ListingInput, type ListingKind } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { SubpageHeader, Toggle } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { useTr } from "../../i18n/tr";
import { haptic } from "../../telegram";
import { marketError, RulesSheet, rulesSeen } from "./parts";
import { shrinkPhoto } from "./photo";

const MAX_PHOTOS = 3;
const ITEM_TYPES = ["books", "toys", "clothes", "school", "sports", "other"] as const;
const CONDITIONS = ["new", "good", "used"] as const;
type Condition = (typeof CONDITIONS)[number];
type FormPhoto = { id: number; thumb_url: string };

/** New listing, or changes to one (which go back to a moderator). */
export function ListingFormScreen() {
  const { id } = useParams();
  const editId = id ? Number(id) : null;
  const existing = useLoad(() => (editId ? api.listing(editId) : Promise.resolve(null)), [editId]);
  const back = useBack(editId ? `/market/${editId}` : "/market");
  const { t } = useTranslation();

  return (
    <main className="screen screen--with-action">
      <SubpageHeader onBack={back} title={t(editId ? "market.form.editTitle" : "market.form.newTitle")} />
      {existing.loading && !existing.data && <InlineLoading />}
      {existing.error !== undefined && <InlineError error={existing.error} onRetry={existing.reload} />}
      {!existing.loading && existing.error === undefined && <Form listing={existing.data ?? null} />}
    </main>
  );
}

function Form({ listing }: { listing: Listing | null }) {
  const { t } = useTranslation();
  const tr = useTr();
  const navigate = useNavigate();
  const points = useLoad(() => api.marketPoints(), []);
  const categories = useLoad(() => api.categories(), []);
  const fileInput = useRef<HTMLInputElement>(null);

  const [rules, setRules] = useState(!listing && !rulesSeen());
  const [kind, setKind] = useState<ListingKind>(listing?.kind ?? "handmade");
  const [photos, setPhotos] = useState<FormPhoto[]>(
    listing?.photos.map((p) => ({ id: p.id, thumb_url: p.thumb_url })) ?? [],
  );
  const [uploading, setUploading] = useState(0);
  const [title, setTitle] = useState(listing?.title ?? "");
  const [description, setDescription] = useState(listing?.description ?? "");
  const [category, setCategory] = useState(listing?.category ?? "");
  const [condition, setCondition] = useState<Condition | "">((listing?.condition as Condition | null) ?? "");
  const [giveaway, setGiveaway] = useState(listing?.giveaway ?? false);
  const [pointId, setPointId] = useState<number | null>(listing?.point?.id ?? null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pointList = points.data ?? [];
  const noPoints = points.data !== undefined && pointList.length === 0;
  const givesAway = kind === "unneeded" || giveaway;

  useEffect(() => {
    // Default to the first point once they are known.
    if (pointId === null && pointList.length > 0) setPointId(pointList[0].id);
  }, [pointList, pointId]);

  function switchKind(value: ListingKind) {
    if (value === kind) return;
    haptic.tap();
    setKind(value);
    setCategory("");
  }

  async function addPhotos(files: FileList | null) {
    if (!files) return;
    const room = MAX_PHOTOS - photos.length - uploading;
    const chosen = Array.from(files).slice(0, Math.max(0, room));
    setError(null);
    setUploading((n) => n + chosen.length);
    for (const file of chosen) {
      try {
        const photo = await api.uploadPhoto(await shrinkPhoto(file));
        setPhotos((prev) => [...prev, { id: photo.id, thumb_url: photo.thumb_url }]);
      } catch (e) {
        setError(marketError(t, e));
      } finally {
        setUploading((n) => n - 1);
      }
    }
  }

  async function submit() {
    if (photos.length === 0) return setError(t("market.form.needPhoto"));
    if (title.trim().length < 3) return setError(t("market.form.needTitle"));
    const body: ListingInput = {
      kind,
      title: title.trim(),
      description: description.trim(),
      category,
      condition: kind === "unneeded" ? (condition as Condition) || null : null,
      giveaway: givesAway,
      pickup_point_id: givesAway ? pointId : null,
      photo_ids: photos.map((p) => p.id),
    };
    setSaving(true);
    setError(null);
    try {
      const saved = listing ? await api.updateListing(listing.id, body) : await api.createListing(body);
      haptic.success();
      navigate(`/market/${saved.id}`, { replace: true, state: { sent: true } });
    } catch (e) {
      haptic.error();
      setError(marketError(t, e));
      setSaving(false);
    }
  }

  const categoryOptions =
    kind === "handmade"
      ? (categories.data ?? []).map((c) => ({ value: c.code, label: `${c.icon} ${tr(c.name)}` }))
      : ITEM_TYPES.map((code) => ({ value: code, label: t(`market.itemType.${code}`) }));
  const ready = photos.length > 0 && title.trim().length >= 3 && category !== "" && uploading === 0;
  const pointMissing = givesAway && (pointId === null || noPoints);
  const conditionMissing = kind === "unneeded" && condition === "";

  return (
    <>
      <form
        className="stack stack--lg"
        onSubmit={(e) => {
          e.preventDefault();
          void submit();
        }}
      >
        <fieldset className="stack">
          <legend className="field__label">{t("market.form.kind")}</legend>
          {(["handmade", "unneeded"] as const).map((value) => (
            <button
              key={value}
              type="button"
              className={kind === value ? "choice is-selected" : "choice"}
              aria-pressed={kind === value}
              disabled={value === "unneeded" && noPoints}
              onClick={() => switchKind(value)}
            >
              <span className="choice__icon" aria-hidden="true">
                <Emoji char={value === "handmade" ? "🎨" : "🎁"} />
              </span>
              <span className="choice__body">
                <span className="choice__title">{t(`market.kind.${value}`)}</span>
                <span className="hint small">{t(`market.kindHint.${value}`)}</span>
              </span>
            </button>
          ))}
        </fieldset>

        <div className="field">
          <span className="field__label">{t("market.form.photos")}</span>
          <div className="photo-picker">
            {photos.map((photo) => (
              <span key={photo.id} className="photo-picker__item">
                <img src={photo.thumb_url} alt="" />
                <button
                  type="button"
                  className="photo-picker__remove"
                  aria-label={t("market.form.removePhoto")}
                  onClick={() => setPhotos((prev) => prev.filter((p) => p.id !== photo.id))}
                >
                  <X size={14} />
                </button>
              </span>
            ))}
            {Array.from({ length: uploading }, (_, i) => (
              <span key={`up-${i}`} className="photo-picker__item photo-picker__item--busy" aria-label={t("market.form.uploading")}>
                <span className="spinner" aria-hidden="true" />
              </span>
            ))}
            {photos.length + uploading < MAX_PHOTOS && (
              <button type="button" className="photo-picker__add" onClick={() => fileInput.current?.click()}>
                <ImagePlus size={24} aria-hidden="true" />
                <span className="small">{t("market.form.addPhoto")}</span>
              </button>
            )}
          </div>
          <input
            ref={fileInput}
            type="file"
            accept="image/*"
            multiple
            hidden
            onChange={(e) => {
              void addPhotos(e.target.files);
              e.target.value = "";
            }}
          />
          <p className="hint small" style={{ marginTop: 6 }}>
            {t("market.form.photosHint")}
          </p>
        </div>

        <label className="field">
          <span className="field__label">{t("market.form.titleLabel")}</span>
          <span className="input-wrap">
            <input
              className="input"
              value={title}
              maxLength={60}
              placeholder={t("market.form.titlePlaceholder")}
              onChange={(e) => setTitle(e.target.value)}
            />
          </span>
        </label>

        <label className="field">
          <span className="field__label">{t("market.form.description")}</span>
          <textarea
            className="textarea"
            value={description}
            maxLength={400}
            rows={3}
            placeholder={t("market.form.descriptionPlaceholder")}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>

        <label className="field">
          <span className="field__label">{t(kind === "handmade" ? "market.form.material" : "market.form.itemType")}</span>
          <select className="select select--block" value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="" disabled>
              —
            </option>
            {categoryOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        {kind === "unneeded" && (
          <fieldset className="field">
            <legend className="field__label">{t("market.form.condition")}</legend>
            <div className="segmented">
              {CONDITIONS.map((value) => (
                <button
                  key={value}
                  type="button"
                  aria-pressed={condition === value}
                  className={condition === value ? "segmented__item is-active" : "segmented__item"}
                  onClick={() => setCondition(value)}
                >
                  {t(`market.condition.${value}`)}
                </button>
              ))}
            </div>
          </fieldset>
        )}

        {kind === "handmade" && (
          <div className="card row row--between">
            <span className="stack" style={{ gap: 2 }}>
              <strong>{t("market.form.giveaway")}</strong>
              <span className="hint small">{t("market.form.giveawayHint")}</span>
            </span>
            <Toggle
              checked={giveaway}
              disabled={noPoints || Boolean(listing?.ready_at_point)}
              label={t("market.form.giveaway")}
              onChange={setGiveaway}
            />
          </div>
        )}

        {noPoints && <p className="note">{t("market.form.noPoints")}</p>}

        {givesAway && pointList.length > 0 && (
          <label className="field">
            <span className="field__label">{t("market.form.point")}</span>
            <select
              className="select select--block"
              value={pointId ?? ""}
              disabled={Boolean(listing?.ready_at_point)}
              onChange={(e) => setPointId(Number(e.target.value))}
            >
              {pointList.map((p) => (
                <option key={p.id} value={p.id}>
                  {tr(p.name)} — {tr(p.address)}
                </option>
              ))}
            </select>
            <span className="hint small">{t("market.form.pointHint")}</span>
          </label>
        )}

        <button type="button" className="link-button" onClick={() => setRules(true)}>
          <BookOpenCheck size={16} aria-hidden="true" /> {t("market.form.rulesLink")}
        </button>
      </form>

      <div className="action-bar">
        {error && (
          <p className="toast toast--error" role="alert">
            {error}
          </p>
        )}
        <button
          type="button"
          className="btn btn--block"
          disabled={!ready || saving || pointMissing || conditionMissing}
          onClick={() => void submit()}
        >
          <Send size={18} aria-hidden="true" /> {t(listing ? "market.form.save" : "market.form.submit")}
        </button>
      </div>

      {rules && <RulesSheet onClose={() => setRules(false)} />}
    </>
  );
}
