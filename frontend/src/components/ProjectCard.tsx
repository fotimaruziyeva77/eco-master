import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import type { ProjectSummary } from "../api/client";
import { useTr } from "../i18n/tr";

export const SAFETY_ICON = { green: "🟢", yellow: "🟡", red: "🔴" } as const;

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
        <span className="hint">
          {SAFETY_ICON[project.safety_level]} {t(`project.difficulty.${project.difficulty}`)} ·{" "}
          {t("common.minutes", { count: project.duration_min })}
        </span>
      </div>
      {project.done && (
        <span className="project-card__done" aria-label={t("project.alreadyDone")}>
          ✓
        </span>
      )}
    </Link>
  );
}
