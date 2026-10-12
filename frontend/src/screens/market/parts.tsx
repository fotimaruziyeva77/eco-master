import { Clock, MapPin, ShieldCheck } from "lucide-react";
import type { TFunction } from "i18next";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { ApiError, type Category, type ListingKind, type ListingStatus, type PickupPoint } from "../../api/client";
import { Emoji } from "../../components/Emoji";
import { formatDay } from "../../i18n/dates";
import { useTr } from "../../i18n/tr";

const RULE_KEYS = ["rule1", "rule2", "rule3", "rule4", "rule5", "rule6"] as const;
const RULES_SEEN_KEY = "ekoustoz.market.rules.v1";

/** Text for a failed market request: a known API code, no connection, or a general error. */
export function marketError(t: TFunction, error: unknown): string {
  if (error instanceof ApiError) {
    const key = `market.errors.${error.code}`;
    return t(key, { defaultValue: t("market.errors.unknown") });
  }
  if (error instanceof Error && error.message.startsWith("photo_")) {
    return t(`market.errors.${error.message}`, { defaultValue: t("market.errors.unknown") });
  }
  return t("errors.network");
}

/** Waste category (handmade) or item type (unneeded) as a label. */
export function useCategoryLabel(categories: Category[] | undefined) {
  const { t } = useTranslation();
  const tr = useTr();
  return (kind: ListingKind, code: string): ReactNode => {
    if (kind === "unneeded") return t(`market.itemType.${code}`, { defaultValue: code });
    const category = categories?.find((c) => c.code === code);
    return category ? (
      <>
        <Emoji char={category.icon} /> {tr(category.name)}
      </>
    ) : (
      code
    );
  };
}

const STATUS_TONE: Record<ListingStatus, string> = {
  pending: "chip chip--amber",
  approved: "chip",
  rejected: "chip chip--danger",
  reserved: "chip chip--sky",
  at_point: "chip chip--sky",
  given: "chip chip--neutral",
  hidden: "chip chip--danger",
};

export function StatusChip({ status }: { status: ListingStatus }) {
  const { t } = useTranslation();
  return <span className={`${STATUS_TONE[status]} chip--sm`}>{t(`market.status.${status}`)}</span>;
}

export function PointCard({ point }: { point: PickupPoint }) {
  const { t } = useTranslation();
  const tr = useTr();
  return (
    <section className="card point-card">
      <span className="icon-tile icon-tile--sky" aria-hidden="true">
        <MapPin size={22} />
      </span>
      <div className="stack" style={{ gap: 4 }}>
        <span className="hint small">{t("market.point")}</span>
        <strong>{tr(point.name)}</strong>
        <span className="text-2">{tr(point.address)}</span>
        <span className="hint small row">
          <Clock size={14} aria-hidden="true" /> {t("market.hours", { hours: tr(point.hours) })}
        </span>
      </div>
    </section>
  );
}

/** The six digits a child says at the handover point. */
export function CodeBox({ code }: { code: string }) {
  return (
    <div className="code-box" aria-label={code.split("").join(" ")}>
      {code.slice(0, 3)}
      <span aria-hidden="true"> </span>
      {code.slice(3)}
    </div>
  );
}

export function SafetyNote() {
  const { t } = useTranslation();
  return (
    <p className="hint small row" style={{ alignItems: "flex-start" }}>
      <ShieldCheck size={16} aria-hidden="true" style={{ flex: "none", marginTop: 2 }} />
      {t("market.handover.safety")}
    </p>
  );
}

export function rulesSeen(): boolean {
  try {
    return localStorage.getItem(RULES_SEEN_KEY) === "1";
  } catch {
    return false;
  }
}

function markRulesSeen(): void {
  try {
    localStorage.setItem(RULES_SEEN_KEY, "1");
  } catch {
    // Private mode: the rules simply show again next time.
  }
}

export function RulesSheet({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation();
  const close = () => {
    markRulesSeen();
    onClose();
  };
  return (
    <div className="overlay" role="dialog" aria-modal="true" aria-label={t("market.rules.title")} onClick={close}>
      <div className="sheet stack" onClick={(e) => e.stopPropagation()}>
        <h2>{t("market.rules.title")}</h2>
        <p className="text-2">{t("market.rules.intro")}</p>
        <ol className="rules-list">
          {RULE_KEYS.map((key) => (
            <li key={key}>{t(`market.rules.${key}`)}</li>
          ))}
        </ol>
        <button type="button" className="btn btn--block" onClick={close}>
          {t("market.rules.ok")}
        </button>
      </div>
    </div>
  );
}

/** A day the user can read, in the app language. */
export function useShortDate() {
  const { i18n } = useTranslation();
  return (value: string | null | undefined) => (value ? formatDay(new Date(value), i18n.language) : "");
}
