import { Share2 } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { api, type ShareKind } from "../api/client";
import { haptic, shareToChat } from "../telegram";

type Props = {
  kind: ShareKind;
  /** Project slug, badge code or "correct/total" for game results. */
  objectId?: string;
  label?: string;
  className?: string;
};

/** Shares a ready message about the user's result to a Telegram chat (TZ 8.11). */
export function ShareButton({ kind, objectId, label, className = "btn btn--soft btn--block" }: Props) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);

  async function share() {
    haptic.tap();
    setBusy(true);
    setFailed(false);
    try {
      await shareToChat(await api.share(kind, objectId));
    } catch {
      haptic.error();
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className={className} disabled={busy} onClick={() => void share()}>
        <Share2 size={18} aria-hidden="true" /> {label ?? t("share.button")}
      </button>
      {failed && (
        <p className="error-text small" role="alert">
          {t("share.error")}
        </p>
      )}
    </>
  );
}
