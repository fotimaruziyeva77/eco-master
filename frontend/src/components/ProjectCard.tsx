import { CircleCheck } from "lucide-react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { ProjectSummary } from "../api/client";
import { useTr } from "../i18n/tr";

export const SAFETY_ICON = { green: "🟢", yellow: "🟡", red: "🔴" } as const;
/** Same value as PROJECT_DONE_POINTS on the server (TZ 8.6). */
export const PROJECT_POINTS = 15;

export function ProjectCard({ project, icon }: { project: ProjectSummary; icon: string }) {
  const { t } = useTranslation();
  const tr = useTr();
  return (
    <Link className="project-card" to={`/projects/${project.slug}`}>
      <div className="project-card__poster" aria-hidden="true">
        {project.poster_url ? <img src={project.poster_url} alt="" loading="lazy" /> : icon}
      </div>
      <div className="project-card__body">
        <strong>{tr(project.title)}</strong>
        <div className="chips">
          <span className="chip chip--sm chip--neutral">
            {SAFETY_ICON[project.safety_level]} {t(`project.difficulty.${project.difficulty}`)}
          </span>
          <span className="chip chip--sm chip--neutral">⏱ {t("common.minutes", { count: project.duration_min })}</span>
        </div>
        {project.done ? (
          <span className="ok-text small row">
            <CircleCheck size={14} /> {t("project.alreadyDone")}
          </span>
        ) : (
          <span className="chip chip--sm chip--amber" style={{ alignSelf: "flex-start" }}>
            +{t("home.points", { count: PROJECT_POINTS })}
          </span>
        )}
      </div>
    </Link>
  );
}
