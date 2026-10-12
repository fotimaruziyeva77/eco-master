import { LogOut } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { api } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { SubpageHeader } from "../../components/ui";
import { useBack } from "../../hooks/useBack";
import { useLoad } from "../../hooks/useLoad";
import { haptic } from "../../telegram";
import { BoardRow, TaskRow } from "./parts";

/** The pupil's class: the teacher's tasks, the class board of this week, leaving. */
export function MyClassScreen() {
  const { t } = useTranslation();
  const back = useBack("/rating");
  const navigate = useNavigate();
  const data = useLoad(() => api.myClass(), []);
  const [leaving, setLeaving] = useState(false);
  const [busy, setBusy] = useState(false);
  const mine = data.data;

  async function leave() {
    setBusy(true);
    try {
      await api.leaveClass();
      haptic.success();
      navigate("/rating", { replace: true });
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="screen">
      <SubpageHeader onBack={back} title={mine?.name ?? t("classes.mine")} />
      {data.loading && data.data === undefined && <InlineLoading />}
      {data.error !== undefined && data.data === undefined && <InlineError error={data.error} onRetry={data.reload} />}
      {data.data === null && <p className="empty">{t("classes.none")}</p>}
      {mine && (
        <div className="stack stack--lg">
          {mine.teacher_nickname && (
            <p className="text-2 row">
              <Emoji char="👩‍🏫" /> {t("classes.join.teacher", { name: `@${mine.teacher_nickname}` })}
            </p>
          )}
          {mine.tasks.length > 0 && (
            <section className="stack">
              <h2>{t("classes.tasks")}</h2>
              <ul className="list">
                {mine.tasks.map((task) => (
                  <li key={task.id}>
                    <TaskRow task={task} />
                  </li>
                ))}
              </ul>
            </section>
          )}
          <section className="stack">
            <h2>{t("classes.board")}</h2>
            <ol className="list">
              {mine.members.map((member) => (
                <li key={member.user_id}>
                  <BoardRow member={member} />
                </li>
              ))}
            </ol>
          </section>
          <button type="button" className="link-button" onClick={() => setLeaving(true)}>
            <LogOut size={16} /> {t("classes.leave")}
          </button>
        </div>
      )}
      {leaving && (
        <div className="overlay" role="dialog" aria-modal="true" onClick={() => setLeaving(false)}>
          <div className="sheet stack" onClick={(e) => e.stopPropagation()}>
            <h2>{t("classes.leave")}</h2>
            <p className="text-2">{t("classes.leaveText")}</p>
            <button type="button" className="btn btn--block btn--danger" disabled={busy} onClick={() => void leave()}>
              {t("classes.leave")}
            </button>
            <button type="button" className="link-button" onClick={() => setLeaving(false)}>
              {t("common.cancel")}
            </button>
          </div>
        </div>
      )}
    </main>
  );
}
