import { ArrowDown, ArrowUp, ExternalLink, Plus, Trash2 } from "lucide-react";
import type { ReactNode } from "react";

import type { FieldSpec, Values } from "./api";

export const LANGS = ["uz", "ru", "en"] as const;
export type Lang = (typeof LANGS)[number];
export const LANG_LABEL: Record<Lang, string> = { uz: "O'zbekcha", ru: "Русский", en: "English" };

type Localized = Partial<Record<Lang, unknown>>;
export type PlanStep = { minutes: number | null; title: string; text: string };

export const isI18n = (spec: FieldSpec) => spec.kind.startsWith("i18n_");

/** An empty value of the right shape, for new items. */
export function emptyValue(spec: FieldSpec): unknown {
  if (spec.kind === "i18n_text" || spec.kind === "i18n_textarea") return { uz: "", ru: "", en: "" };
  if (spec.kind === "i18n_list" || spec.kind === "i18n_plan") return { uz: [], ru: [], en: [] };
  if (spec.kind === "bool") return false;
  return null;
}

export function filled(value: unknown): boolean {
  if (Array.isArray(value)) {
    return value.some((v) => (typeof v === "string" ? v.trim() : v && (v as PlanStep).title?.trim()));
  }
  return typeof value === "string" ? value.trim() !== "" : value !== null && value !== undefined;
}

/** Required multilingual fields still empty in a language (for the language tabs). */
export function missingIn(fields: FieldSpec[], values: Values, lang: Lang): number {
  return fields.filter((f) => f.required && isI18n(f) && !filled((values[f.name] as Localized)?.[lang])).length;
}

type Props = {
  spec: FieldSpec;
  value: unknown;
  lang: Lang;
  error?: string;
  locked?: boolean;
  onChange: (value: unknown) => void;
};

export function FieldEditor({ spec, value, lang, error, locked, onChange }: Props) {
  const id = `f-${spec.name}`;
  const localized = (value ?? {}) as Localized;
  const setLang = (v: unknown) => onChange({ ...localized, [lang]: v });
  const invalid = error ? " is-invalid" : "";

  let input: ReactNode;
  switch (spec.kind) {
    case "i18n_text":
      input = (
        <input
          id={id}
          className={`a-input${invalid}`}
          value={(localized[lang] as string) ?? ""}
          maxLength={spec.max_length ?? undefined}
          onChange={(e) => setLang(e.target.value)}
        />
      );
      break;
    case "i18n_textarea":
      input = (
        <textarea
          id={id}
          className={`a-textarea${invalid}`}
          value={(localized[lang] as string) ?? ""}
          maxLength={spec.max_length ?? undefined}
          onChange={(e) => setLang(e.target.value)}
        />
      );
      break;
    case "i18n_list":
      input = <ListEditor items={(localized[lang] as string[]) ?? []} max={spec.max_length} onChange={setLang} />;
      break;
    case "i18n_plan":
      input = <PlanEditor steps={(localized[lang] as PlanStep[]) ?? []} onChange={setLang} />;
      break;
    case "textarea":
      input = (
        <textarea
          id={id}
          className={`a-textarea${invalid}`}
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value || null)}
        />
      );
      break;
    case "int":
      input = (
        <input
          id={id}
          type="number"
          className={`a-input a-input--narrow${invalid}`}
          value={value === null || value === undefined ? "" : String(value)}
          min={spec.min ?? undefined}
          max={spec.max ?? undefined}
          onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
        />
      );
      break;
    case "bool":
      return (
        <div className="a-field">
          <label className="a-check">
            <input type="checkbox" checked={Boolean(value)} onChange={(e) => onChange(e.target.checked)} />
            {spec.label}
          </label>
          {spec.help && <span className="a-help">{spec.help}</span>}
        </div>
      );
    case "date":
      input = (
        <input
          id={id}
          type="date"
          className={`a-input a-input--narrow${invalid}`}
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value || null)}
        />
      );
      break;
    case "color":
      input = (
        <div className="a-row">
          <input
            type="color"
            value={(value as string) || "#10B981"}
            aria-label={spec.label}
            onChange={(e) => onChange(e.target.value.toUpperCase())}
            style={{ width: 44, height: 38, border: 0, background: "none", padding: 0 }}
          />
          <input
            id={id}
            className={`a-input a-input--narrow${invalid}`}
            value={(value as string) ?? ""}
            onChange={(e) => onChange(e.target.value || null)}
          />
        </div>
      );
      break;
    case "select":
    case "category":
      input = (
        <select
          id={id}
          className={`a-select${invalid}`}
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value || null)}
        >
          {(spec.nullable || value === null) && (
            <option value="">{spec.kind === "category" && spec.nullable ? "Umumiy ekologiya" : "— tanlang —"}</option>
          )}
          {spec.options?.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
      );
      break;
    default:
      // text, url, emoji
      input = (
        <div className="a-row" style={{ flexWrap: "nowrap" }}>
          <input
            id={id}
            type={spec.kind === "url" ? "url" : "text"}
            className={`a-input${spec.kind === "emoji" ? " a-input--narrow" : ""}${invalid}`}
            value={(value as string) ?? ""}
            disabled={locked}
            maxLength={spec.max_length ?? undefined}
            spellCheck={spec.kind === "text"}
            onChange={(e) => onChange(e.target.value || null)}
          />
          {spec.kind === "url" && typeof value === "string" && value.startsWith("https://") && (
            <a className="a-icon-btn" href={value} target="_blank" rel="noreferrer" aria-label="Havolani ochish">
              <ExternalLink size={15} />
            </a>
          )}
        </div>
      );
  }

  return (
    <div className="a-field" id={`field-${spec.name}`}>
      <label className="a-label" htmlFor={id}>
        {spec.label}
        {isI18n(spec) && <span className="a-pill a-pill--draft">{lang.toUpperCase()}</span>}
        {spec.required && <span className="a-req">*</span>}
        {locked && <span className="a-pill a-pill--warn">o'zgarmaydi</span>}
      </label>
      {input}
      {spec.help && <span className="a-help">{spec.help}</span>}
      {error && <span className="a-error">{error}</span>}
    </div>
  );
}

function move<T>(items: T[], from: number, to: number): T[] {
  const next = [...items];
  const [item] = next.splice(from, 1);
  next.splice(to, 0, item);
  return next;
}

function RowActions({ index, count, onMove, onRemove }: { index: number; count: number; onMove: (to: number) => void; onRemove: () => void }) {
  return (
    <span className="a-list-actions">
      <button type="button" className="a-icon-btn" disabled={index === 0} onClick={() => onMove(index - 1)} aria-label="Yuqoriga">
        <ArrowUp size={14} />
      </button>
      <button type="button" className="a-icon-btn" disabled={index === count - 1} onClick={() => onMove(index + 1)} aria-label="Pastga">
        <ArrowDown size={14} />
      </button>
      <button type="button" className="a-icon-btn" onClick={onRemove} aria-label="O'chirish">
        <Trash2 size={14} />
      </button>
    </span>
  );
}

function ListEditor({ items, max, onChange }: { items: string[]; max?: number | null; onChange: (items: string[]) => void }) {
  return (
    <div className="a-list">
      {items.map((item, i) => (
        <div key={i} className="a-list-row">
          <span className="a-list-num">{i + 1}.</span>
          <textarea
            className="a-textarea"
            style={{ minHeight: 38 }}
            rows={1}
            value={item}
            maxLength={max ?? undefined}
            onChange={(e) => onChange(items.map((v, j) => (j === i ? e.target.value : v)))}
          />
          <RowActions
            index={i}
            count={items.length}
            onMove={(to) => onChange(move(items, i, to))}
            onRemove={() => onChange(items.filter((_, j) => j !== i))}
          />
        </div>
      ))}
      <button type="button" className="a-btn a-btn--soft a-btn--sm" style={{ justifySelf: "start" }} onClick={() => onChange([...items, ""])}>
        <Plus size={14} /> Qo'shish
      </button>
    </div>
  );
}

function PlanEditor({ steps, onChange }: { steps: PlanStep[]; onChange: (steps: PlanStep[]) => void }) {
  const total = steps.reduce((sum, s) => sum + (s.minutes ?? 0), 0);
  const update = (i: number, patch: Partial<PlanStep>) =>
    onChange(steps.map((s, j) => (j === i ? { ...s, ...patch } : s)));
  return (
    <div className="a-list">
      {steps.map((step, i) => (
        <div key={i} className="a-plan-row">
          <input
            type="number"
            className="a-input"
            min={1}
            max={90}
            aria-label="Daqiqa"
            value={step.minutes ?? ""}
            onChange={(e) => update(i, { minutes: e.target.value === "" ? null : Number(e.target.value) })}
          />
          <div className="a-stack">
            <input className="a-input" placeholder="Bosqich nomi" value={step.title} onChange={(e) => update(i, { title: e.target.value })} />
            <textarea className="a-textarea" placeholder="Nima qilinadi" value={step.text} onChange={(e) => update(i, { text: e.target.value })} />
          </div>
          <RowActions
            index={i}
            count={steps.length}
            onMove={(to) => onChange(move(steps, i, to))}
            onRemove={() => onChange(steps.filter((_, j) => j !== i))}
          />
        </div>
      ))}
      <div className="a-row">
        <button type="button" className="a-btn a-btn--soft a-btn--sm" onClick={() => onChange([...steps, { minutes: 5, title: "", text: "" }])}>
          <Plus size={14} /> Bosqich qo'shish
        </button>
        <span className={total === 45 ? "a-pill a-pill--ok" : "a-pill a-pill--warn"}>Jami: {total} daqiqa</span>
      </div>
    </div>
  );
}
