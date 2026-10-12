import type { TFunction } from "i18next";
import { Check } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { ApiError, type ClassTask, type RankedMember } from "../../api/client";
import { Emoji } from "../../components/Emoji";
import { Avatar, LEVEL_EMOJI, ProgressBar } from "../../components/ui";
import { formatDay } from "../../i18n/dates";
import { useTr } from "../../i18n/tr";

/** Text for a failed class request: a known code, no connection, or a general error. */
export function classError(t: TFunction, error: unknown): string {
  if (error instanceof ApiError) {
    const code = error.code === "contact_not_allowed" || error.code === "text_not_allowed" ? "name" : error.code;
    return t(`classes.errors.${code}`, { defaultValue: t("classes.errors.unknown") });
  }
  return t("errors.network");
}

/** "by Friday 17 October", or "overdue". */
export function useDue() {
  const { t, i18n } = useTranslation();
  return (due: string) => {
    const day = new Date(`${due}T00:00:00`);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (day < today) return t("classes.overdue");
    return t("classes.dueBy", { date: formatDay(day, i18n.language, true) });
  };
}

/** One row of a class or league board. */
export function BoardRow({ member, marker }: { member: RankedMember; marker?: "up" | "down" }) {
  const { t } = useTranslation();
  const classes = ["rank-row", member.is_me && "is-me", marker && `rank-row--${marker}`].filter(Boolean).join(" ");
  return (
    <div className={classes}>
      <span className="rank-row__place">{member.rank}</span>
      <Avatar id={member.user_id} />
      <span className="rank-row__name">
        <strong>
          {member.nickname ? `@${member.nickname}` : t("market.anonymous")}{" "}
          {member.is_me && <span className="chip chip--sm">{t("rating.you")}</span>}
        </strong>
        <span className="hint small">
          <Emoji char={LEVEL_EMOJI[member.level_code]} /> {t(`levels.${member.level_code}`)}
        </span>
      </span>
      <span className="rank-row__points">
        <Emoji char="⭐" /> {member.points}
      </span>
    </div>
  );
}

/** A class task: the project, the day it is due and, for the teacher, how many did it. */
export function TaskRow({ task, teacher }: { task: ClassTask; teacher?: boolean }) {
  const tr = useTr();
  const due = useDue();
  return (
    <Link className="list-row task-row" to={`/projects/${task.project_slug}`}>
      <span className="icon-tile" aria-hidden="true">
        <Emoji char={task.icon} />
      </span>
      <span className="list-row__text">
        <strong>{tr(task.title)}</strong>
        <span className="hint small">{due(task.due_date)}</span>
        {teacher && (
          <span className="task-row__progress">
            <ProgressBar value={task.done_count} max={Math.max(1, task.member_count)} thin />
            <span className="small strong">
              {task.done_count}/{task.member_count}
            </span>
          </span>
        )}
      </span>
      {!teacher && task.done && (
        <span className="chip chip--sm">
          <Check size={14} />
        </span>
      )}
    </Link>
  );
}
