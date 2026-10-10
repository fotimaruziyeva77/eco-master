import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading, SubpageHeader } from "../components/common";
import { ProjectCard } from "../components/ProjectCard";
import { useBack } from "../hooks/useBack";
import { useLoad } from "../hooks/useLoad";
import { useTr } from "../i18n/tr";

export function CategoryScreen() {
  const { code = "" } = useParams();
  const { t } = useTranslation();
  const tr = useTr();
  const back = useBack("/learn");
  const data = useLoad(() => api.category(code), [code]);
  const category = data.data?.category;

  return (
    <main className="screen">
      <SubpageHeader
        onBack={back}
        title={category && `${category.icon} ${tr(category.name)}`}
      />
      {data.loading && !data.data && <InlineLoading />}
      {data.error !== undefined && !data.data && <InlineError error={data.error} onRetry={data.reload} />}
      {data.data && data.data.projects.length === 0 && (
        <p className="empty">{t("category.empty")}</p>
      )}
      {data.data && (
        <div className="project-list">
          {data.data.projects.map((project) => (
            <ProjectCard key={project.slug} project={project} icon={data.data!.category.icon} />
          ))}
        </div>
      )}
    </main>
  );
}
