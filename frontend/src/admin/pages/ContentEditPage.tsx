import { AlertTriangle, ArrowLeft, CircleAlert, FileDown, Trash2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import {
  AdminApiError,
  adminApi,
  errorText,
  lessonPdfUrl,
  type ContentItem,
  type ContentStatus,
  type FieldSpec,
  type Issue,
  type Values,
} from "../api";
import { emptyValue, FieldEditor, LANG_LABEL, LANGS, missingIn, type Lang } from "../fields";
import { Preview } from "../preview";
import { ConfirmModal, LoadError, Loading, STATUS_LABEL, StatusPill, useToast } from "../ui";

/** Status buttons per status (TZ 8.12: Draft → In review → Published → Archive). */
const ACTIONS: Record<ContentStatus, { to: ContentStatus; label: string; kind: string }[]> = {
  draft: [
    { to: "review", label: "Tekshiruvga yuborish", kind: "a-btn a-btn--sky" },
    { to: "published", label: "Nashr qilish", kind: "a-btn a-btn--soft" },
  ],
  review: [
    { to: "published", label: "Nashr qilish", kind: "a-btn a-btn--soft" },
    { to: "draft", label: "Qoralamaga qaytarish", kind: "a-btn a-btn--ghost" },
  ],
  published: [
    { to: "draft", label: "Nashrdan olish", kind: "a-btn a-btn--ghost" },
    { to: "archived", label: "Arxivlash", kind: "a-btn a-btn--amber" },
  ],
  archived: [{ to: "draft", label: "Qoralamaga qaytarish", kind: "a-btn a-btn--ghost" }],
};

function freshValues(fields: FieldSpec[], defaults: Record<string, unknown>): Values {
  const values: Values = {};
  for (const f of fields) {
    values[f.name] = f.kind === "int" && !f.nullable ? (f.min ?? 0) : emptyValue(f);
  }
  return { ...values, ...defaults };
}

/** Values an upload fills in: an empty field, or a cover taken from an earlier video. */
function withUploads(values: Values | null, patch: Record<string, string>): Values | null {
  if (!values) return values;
  const next = { ...values };
  for (const [name, url] of Object.entries(patch)) {
    const current = values[name];
    if (!current || (typeof current === "string" && current.startsWith("/media/v/"))) next[name] = url;
  }
  return next;
}

function displayTitle(fields: FieldSpec[], values: Values | null): string {
  const first = fields.find((f) => f.kind === "i18n_text");
  const title = first && values ? (values[first.name] as Record<string, string> | null) : null;
  return title?.uz || title?.ru || title?.en || "(nomsiz)";
}

export function ContentEditPage() {
  const { type = "", id } = useParams();
  const isNew = id === undefined;
  const itemId = isNew ? null : Number(id);
  const navigate = useNavigate();
  const toast = useToast();
  const meta = useLoad(() => adminApi.contentMeta(type), [type]);

  const [item, setItem] = useState<ContentItem | null>(null);
  const [values, setValues] = useState<Values | null>(null);
  const [saved, setSaved] = useState("");
  const [lang, setLang] = useState<Lang>("uz");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [blocked, setBlocked] = useState<Issue[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<unknown>();
  const [deleting, setDeleting] = useState(false);

  function accept(next: ContentItem) {
    setItem(next);
    setValues(next.values);
    setSaved(JSON.stringify(next.values));
  }

  useEffect(() => {
    if (!meta.data) return;
    setErrors({});
    setBlocked(null);
    setLoadError(undefined);
    if (itemId === null) {
      const fresh = freshValues(meta.data.fields, meta.data.defaults);
      setItem(null);
      setValues(fresh);
      setSaved(JSON.stringify(fresh));
      return;
    }
    adminApi.contentItem(type, itemId).then(accept, setLoadError);
  }, [meta.data, type, itemId]);

  const dirty = values !== null && JSON.stringify(values) !== saved;
  useEffect(() => {
    if (!dirty) return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const fields = meta.data?.fields ?? [];
  const missing = useMemo(
    () => Object.fromEntries(LANGS.map((l) => [l, values ? missingIn(fields, values, l) : 0])),
    [fields, values],
  ) as Record<Lang, number>;

  if (meta.error !== undefined) return <LoadError error={meta.error} onRetry={meta.reload} />;
  if (loadError !== undefined) return <LoadError error={loadError} />;
  if (!meta.data || !values) return <Loading />;
  const info = meta.data;

  async function save(): Promise<ContentItem | null> {
    setBusy(true);
    setErrors({});
    setBlocked(null);
    try {
      const result =
        itemId === null
          ? await adminApi.contentCreate(type, values!)
          : await adminApi.contentUpdate(type, itemId, values!);
      accept(result);
      toast("Saqlandi");
      if (itemId === null) navigate(`/content/${type}/${result.id}`, { replace: true });
      return result;
    } catch (e) {
      if (e instanceof AdminApiError) {
        setErrors(e.fieldErrors);
        if (e.issues.length) setBlocked(e.issues);
      }
      toast(errorText(e));
      return null;
    } finally {
      setBusy(false);
    }
  }

  async function changeStatus(next: ContentStatus) {
    let current = item;
    if (dirty) current = await save();
    if (!current) return;
    setBusy(true);
    setBlocked(null);
    try {
      accept(await adminApi.contentStatus(type, current.id, next));
      toast(`Holat: ${STATUS_LABEL[next]}`);
    } catch (e) {
      if (e instanceof AdminApiError && e.issues.length) setBlocked(e.issues);
      toast(errorText(e));
    } finally {
      setBusy(false);
    }
  }

  function focusIssue(issue: Issue) {
    if (issue.lang && (LANGS as readonly string[]).includes(issue.lang)) setLang(issue.lang as Lang);
    window.setTimeout(() => {
      document.getElementById(`field-${issue.field}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }

  const issues = blocked ?? item?.issues ?? [];
  const status = item?.status ?? null;
  const fixedLocked = !isNew && (!info.has_status || status !== "draft");

  return (
    <>
      <div className="a-bar">
        <Link to={`/content/${type}`} className="a-icon-btn" aria-label="Ro'yxatga qaytish">
          <ArrowLeft size={16} />
        </Link>
        <h1>{isNew ? `Yangi — ${info.title}` : displayTitle(fields, values)}</h1>
        <StatusPill status={status} />
        {dirty && <span className="a-pill a-pill--warn">Saqlanmagan</span>}
        <button type="button" className="a-btn" disabled={busy || !dirty} onClick={() => void save()}>
          Saqlash
        </button>
        {info.has_status &&
          status &&
          ACTIONS[status].map((a) => (
            <button key={a.to} type="button" className={a.kind} disabled={busy} onClick={() => void changeStatus(a.to)}>
              {a.label}
            </button>
          ))}
      </div>

      <div className="a-editor">
        <div>
          <div className="a-toolbar">
            <div className="a-tabs" role="tablist" aria-label="Til">
              {LANGS.map((l) => (
                <button key={l} type="button" role="tab" aria-selected={lang === l} className={lang === l ? "a-tab active" : "a-tab"} onClick={() => setLang(l)}>
                  <span className={missing[l] ? "a-dot a-dot--missing" : "a-dot"} aria-hidden="true" />
                  {LANG_LABEL[l]}
                  {missing[l] > 0 && <small>{missing[l]} bo'sh</small>}
                </button>
              ))}
            </div>
            {type === "lessons" && item && (
              <span className="a-row a-small">
                <FileDown size={16} className="a-muted" aria-hidden="true" /> PDF:
                {LANGS.map((l) => (
                  <a key={l} className="a-btn a-btn--ghost a-btn--sm" href={lessonPdfUrl(item.id, l)} target="_blank" rel="noreferrer">
                    {l.toUpperCase()}
                  </a>
                ))}
              </span>
            )}
          </div>

          {issues.length > 0 && (
            <div className="a-issues">
              {dirty && !blocked && <span className="a-help">Tekshiruv natijasi saqlangandan keyin yangilanadi.</span>}
              {issues.map((issue, i) => (
                <button key={i} type="button" className={`a-issue a-issue--${issue.level}`} onClick={() => focusIssue(issue)}>
                  {issue.level === "error" ? <CircleAlert size={16} /> : <AlertTriangle size={16} />}
                  <span>{issue.message}</span>
                </button>
              ))}
            </div>
          )}

          <div className="a-card">
            {fields.map((spec) => (
              <FieldEditor
                key={spec.name}
                spec={spec}
                value={values[spec.name]}
                lang={lang}
                error={errors[spec.name]}
                locked={spec.fixed && fixedLocked}
                onChange={(v) => setValues((prev) => ({ ...prev, [spec.name]: v }))}
                onExtra={(patch) => setValues((prev) => withUploads(prev, patch))}
                values={values}
              />
            ))}
          </div>

          {info.deletable && status === "draft" && (
            <button type="button" className="a-btn a-btn--danger" style={{ marginTop: 16 }} onClick={() => setDeleting(true)}>
              <Trash2 size={16} /> Qoralamani o'chirish
            </button>
          )}
        </div>

        <aside className="a-preview" aria-label="Oldindan ko'rish">
          <div className="a-row" style={{ justifyContent: "space-between" }}>
            <strong>Ilovada ko'rinishi</strong>
            <span className="a-muted a-small">{LANG_LABEL[lang]}</span>
          </div>
          <div className="a-phone">
            <div className="screen">
              <Preview kind={info.preview} values={values} lang={lang} fields={fields} />
            </div>
          </div>
        </aside>
      </div>

      {deleting && item && (
        <ConfirmModal
          title="Qoralamani o'chirish"
          text="Bu qoralama butunlay o'chiriladi."
          confirm="O'chirish"
          danger
          onClose={() => setDeleting(false)}
          onConfirm={async () => {
            await adminApi.contentDelete(type, item.id);
            toast("O'chirildi");
            navigate(`/content/${type}`, { replace: true });
          }}
        />
      )}
    </>
  );
}
