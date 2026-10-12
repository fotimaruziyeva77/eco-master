import { ChevronRight, Plus } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router";

import { api } from "../../api/client";
import { InlineError, InlineLoading } from "../../components/common";
import { Emoji } from "../../components/Emoji";
import { useLoad } from "../../hooks/useLoad";
import { haptic } from "../../telegram";
import { NameSheet } from "./ClassScreen";
import { classError } from "./parts";

/** "My classes" on the teachers' screen: the list and a new class in one step. */
export function TeacherClasses() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const classes = useLoad(() => api.classes(), []);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function create(name: string) {
    setError(null);
    try {
      const made = await api.createClass(name);
      haptic.success();
      navigate(`/classes/${made.id}`);
    } catch (e) {
      haptic.error();
      setError(classError(t, e));
    }
  }

  return (
    <section className="stack">
      <div className="section-head">
        <h2>{t("classes.title")}</h2>
        <button
          type="button"
          className="btn btn--soft btn--sm"
          onClick={() => {
            setError(null);
            setCreating(true);
          }}
        >
          <Plus size={16} /> {t("classes.new")}
        </button>
      </div>
      {classes.loading && !classes.data && <InlineLoading />}
      {classes.error !== undefined && !classes.data && <InlineError error={classes.error} onRetry={classes.reload} />}
      {classes.data?.length === 0 && <p className="hint">{t("classes.empty")}</p>}
      <ul className="list">
        {classes.data?.map((c) => (
          <li key={c.id}>
            <Link className="list-row" to={`/classes/${c.id}`}>
              <span className="icon-tile icon-tile--sky" aria-hidden="true">
                <Emoji char="🏫" />
              </span>
              <span className="list-row__text">
                <strong>{c.name}</strong>
                <span className="hint small">{t("classes.members", { count: c.member_count })}</span>
              </span>
              <ChevronRight className="list-row__chevron" size={20} />
            </Link>
          </li>
        ))}
      </ul>
      {creating && <NameSheet initial="" error={error} onClose={() => setCreating(false)} onSave={create} />}
    </section>
  );
}
