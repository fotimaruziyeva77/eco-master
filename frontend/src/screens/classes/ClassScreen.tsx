import { Check, Copy, Pencil, Plus, Share2, Trash2, X } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate, useParams } from "react-router";

import { api, type ClassDetail, type ClassMember } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { QrCode } from "../../components/QrCode";
import { Avatar, LEVEL_EMOJI, SubpageHeader } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { useTr } from "../../i18n/tr";
import { haptic, openTelegramLink } from "../../telegram";
import { classError, TaskRow } from "./parts";

type Sheet = { kind: "rename" } | { kind: "task" } | { kind: "delete" } | { kind: "remove"; member: ClassMember } | null;

/** A teacher's class: the invitation, the tasks and the pupils with their points this week. */
export function ClassScreen() {
  const { id = "" } = useParams();
  const { t } = useTranslation();
  const back = useBack("/teachers");
  const navigate = useNavigate();
  const data = useLoad(() => api.classDetail(Number(id)), [id]);
  const [sheet, setSheet] = useState<Sheet>(null);
  const [error, setError] = useState<string | null>(null);
  const detail = data.data;

  async function run(action: () => Promise<unknown>, after?: () => void) {
    setError(null);
    try {
      await action();
      haptic.success();
      setSheet(null);
      if (after) after();
      else data.reload();
    } catch (e) {
      haptic.error();
      setError(classError(t, e));
    }
  }

  return (
    <main className="screen">
      <SubpageHeader
        onBack={back}
        title={detail?.name ?? t("classes.title")}
        right={
          detail && (
            <button type="button" className="icon-button" onClick={() => setSheet({ kind: "rename" })} aria-label={t("classes.rename")}>
              <Pencil size={18} />
            </button>
          )
        }
      />
      {data.loading && !detail && <InlineLoading />}
      {data.error !== undefined && !detail && <InlineError error={data.error} onRetry={data.reload} />}

      {detail && (
        <div className="stack stack--lg">
          <Invite detail={detail} />

          <section className="stack">
            <div className="section-head">
              <h2>{t("classes.tasks")}</h2>
              <button type="button" className="btn btn--soft btn--sm" onClick={() => setSheet({ kind: "task" })}>
                <Plus size={16} /> {t("classes.addTask")}
              </button>
            </div>
            {detail.tasks.length === 0 && <p className="hint">{t("classes.noTasks")}</p>}
            <ul className="list">
              {detail.tasks.map((task) => (
                <li key={task.id} className="task-row__wrap">
                  <TaskRow task={task} teacher />
                  <button
                    type="button"
                    className="icon-button task-row__delete"
                    aria-label={t("classes.deleteTask")}
                    onClick={() => void run(() => api.deleteClassTask(detail.id, task.id))}
                  >
                    <Trash2 size={16} />
                  </button>
                </li>
              ))}
            </ul>
          </section>

          <section className="stack">
            <h2>
              {t("classes.pupils")} <span className="hint">{detail.member_count}</span>
            </h2>
            {detail.members.length === 0 && <p className="hint">{t("classes.noMembers")}</p>}
            <ul className="list">
              {detail.members.map((member, i) => (
                <li key={member.user_id}>
                  <div className="rank-row">
                    <span className="rank-row__place">{i + 1}</span>
                    <Avatar id={member.user_id} />
                    <span className="rank-row__name">
                      <strong>{member.nickname ? `@${member.nickname}` : t("market.anonymous")}</strong>
                      <span className="hint small">
                        <Emoji char={LEVEL_EMOJI[member.level_code]} /> {t(`levels.${member.level_code}`)} ·{" "}
                        <Emoji char="🔨" /> {member.projects_done}
                      </span>
                    </span>
                    <span className="rank-row__points">
                      <Emoji char="⭐" /> {member.points_week}
                    </span>
                    <button
                      type="button"
                      className="icon-button"
                      aria-label={t("classes.remove")}
                      onClick={() => setSheet({ kind: "remove", member })}
                    >
                      <X size={16} />
                    </button>
                  </div>
                </li>
              ))}
            </ul>
            <p className="hint small">{t("classes.weekPoints")}</p>
          </section>

          <button type="button" className="link-button error-text" onClick={() => setSheet({ kind: "delete" })}>
            <Trash2 size={16} /> {t("classes.delete")}
          </button>
        </div>
      )}

      {error && !sheet && (
        <p className="toast toast--error" role="alert">
          {error}
        </p>
      )}

      {detail && sheet?.kind === "rename" && (
        <NameSheet
          initial={detail.name}
          error={error}
          onClose={() => setSheet(null)}
          onSave={(name) => run(() => api.renameClass(detail.id, name))}
        />
      )}
      {detail && sheet?.kind === "task" && (
        <TaskSheet
          detail={detail}
          error={error}
          onClose={() => setSheet(null)}
          onSave={(slug, due) => run(() => api.addClassTask(detail.id, slug, due))}
        />
      )}
      {detail && sheet?.kind === "remove" && (
        <Confirm
          title={t("classes.remove")}
          text={sheet.member.nickname ? `@${sheet.member.nickname}` : t("market.anonymous")}
          error={error}
          onClose={() => setSheet(null)}
          onConfirm={() => run(() => api.removeMember(detail.id, sheet.member.user_id))}
        />
      )}
      {detail && sheet?.kind === "delete" && (
        <Confirm
          title={t("classes.delete")}
          text={t("classes.deleteText")}
          error={error}
          onClose={() => setSheet(null)}
          onConfirm={() => run(() => api.deleteClass(detail.id), () => navigate("/teachers", { replace: true }))}
        />
      )}
    </main>
  );
}

/** QR code and code to show on the board, and the link to send to the class chat. */
function Invite({ detail }: { detail: ClassDetail }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);
  const [enlarged, setEnlarged] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(detail.link);
      haptic.success();
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // No clipboard access: the code is on the screen anyway.
    }
  }

  function share() {
    const text = t("classes.shareText", { name: detail.name });
    openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(detail.link)}&text=${encodeURIComponent(text)}`);
  }

  return (
    <section className="card stack invite">
      <div>
        <h2>{t("classes.invite")}</h2>
        <p className="hint small">{t("classes.inviteHint")}</p>
      </div>
      <button type="button" className="qr-button" onClick={() => setEnlarged(true)} aria-label={t("teachers.enlarge")}>
        <QrCode value={detail.link} label={t("teachers.qrLabel")} />
      </button>
      <div className="class-code" aria-label={t("classes.code")}>
        {detail.code}
      </div>
      <div className="invite__actions">
        <button type="button" className="btn btn--soft" onClick={() => void copy()}>
          {copied ? <Check size={18} aria-hidden="true" /> : <Copy size={18} aria-hidden="true" />}
          {copied ? t("teachers.copied") : t("teachers.copy")}
        </button>
        <button type="button" className="btn btn--soft" onClick={share}>
          <Share2 size={18} aria-hidden="true" /> {t("share.button")}
        </button>
      </div>
      {enlarged && (
        <div className="overlay overlay--qr" role="dialog" aria-modal="true" onClick={() => setEnlarged(false)}>
          <QrCode value={detail.link} label={t("teachers.qrLabel")} className="qr qr--large" />
          <div className="class-code class-code--large">{detail.code}</div>
          <button type="button" className="btn btn--white" autoFocus onClick={() => setEnlarged(false)}>
            {t("common.close")}
          </button>
        </div>
      )}
    </section>
  );
}

export function NameSheet({
  initial,
  error,
  onClose,
  onSave,
}: {
  initial: string;
  error: string | null;
  onClose: () => void;
  onSave: (name: string) => Promise<void>;
}) {
  const { t } = useTranslation();
  const [name, setName] = useState(initial);
  const [busy, setBusy] = useState(false);
  return (
    <div className="overlay" role="dialog" aria-modal="true" onClick={onClose}>
      <form
        className="sheet stack"
        onClick={(e) => e.stopPropagation()}
        onSubmit={(e) => {
          e.preventDefault();
          setBusy(true);
          void onSave(name).finally(() => setBusy(false));
        }}
      >
        <h2>{initial ? t("classes.rename") : t("classes.new")}</h2>
        <input
          className="input input--boxed"
          value={name}
          maxLength={40}
          placeholder={t("classes.namePlaceholder")}
          autoFocus
          onChange={(e) => setName(e.target.value)}
          aria-label={t("classes.name")}
        />
        {error && <p className="error-text small">{error}</p>}
        <button type="submit" className="btn btn--block" disabled={busy || !name.trim()}>
          {initial ? t("common.save") : t("classes.create")}
        </button>
        <button type="button" className="link-button" onClick={onClose}>
          {t("common.cancel")}
        </button>
      </form>
    </div>
  );
}

function TaskSheet({
  detail,
  error,
  onClose,
  onSave,
}: {
  detail: ClassDetail;
  error: string | null;
  onClose: () => void;
  onSave: (slug: string, due: string) => Promise<void>;
}) {
  const { t } = useTranslation();
  const tr = useTr();
  const projects = useLoad(() => api.projects(), []);
  const categories = useLoad(() => api.categories(), []);
  const given = new Set(detail.tasks.map((task) => task.project_slug));
  const inWeek = new Date(Date.now() + 7 * 86_400_000).toISOString().slice(0, 10);
  const [slug, setSlug] = useState<string | null>(null);
  const [due, setDue] = useState(inWeek);
  const [busy, setBusy] = useState(false);
  const icon = (code: string) => categories.data?.find((c) => c.code === code)?.icon ?? "♻️";

  return (
    <div className="overlay" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="sheet stack sheet--tall" onClick={(e) => e.stopPropagation()}>
        <h2>{t("classes.addTask")}</h2>
        {projects.loading && !projects.data && <InlineLoading />}
        <div className="stack task-picker">
          {projects.data
            ?.filter((p) => !given.has(p.slug))
            .map((p) => (
              <button
                key={p.slug}
                type="button"
                className={slug === p.slug ? "choice is-selected" : "choice"}
                onClick={() => setSlug(p.slug)}
              >
                <span className="choice__icon" aria-hidden="true">
                  <Emoji char={icon(p.category_code)} />
                </span>
                <span className="choice__body">
                  <span className="choice__title">{tr(p.title)}</span>
                  <span className="hint small">{t("common.minutes", { count: p.duration_min })}</span>
                </span>
              </button>
            ))}
        </div>
        <label className="field">
          <span className="field__label">{t("classes.taskDue")}</span>
          <input className="input input--boxed" type="date" value={due} min={new Date().toISOString().slice(0, 10)} onChange={(e) => setDue(e.target.value)} />
        </label>
        {error && <p className="error-text small">{error}</p>}
        <button
          type="button"
          className="btn btn--block"
          disabled={busy || !slug || !due}
          onClick={() => {
            setBusy(true);
            void onSave(slug!, due).finally(() => setBusy(false));
          }}
        >
          {t("classes.addTask")}
        </button>
        <button type="button" className="link-button" onClick={onClose}>
          {t("common.cancel")}
        </button>
      </div>
    </div>
  );
}

function Confirm({
  title,
  text,
  error,
  onClose,
  onConfirm,
}: {
  title: string;
  text: string;
  error: string | null;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}) {
  const { t } = useTranslation();
  const [busy, setBusy] = useState(false);
  return (
    <div className="overlay" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="sheet stack" onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        <p className="text-2">{text}</p>
        {error && <p className="error-text small">{error}</p>}
        <button
          type="button"
          className="btn btn--block btn--danger"
          disabled={busy}
          onClick={() => {
            setBusy(true);
            void onConfirm().finally(() => setBusy(false));
          }}
        >
          <Trash2 size={18} /> {title}
        </button>
        <button type="button" className="link-button" onClick={onClose}>
          {t("common.cancel")}
        </button>
      </div>
    </div>
  );
}
