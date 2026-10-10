import { useTranslation } from "react-i18next";
import { useParams } from "react-router";

import { api } from "../api/client";
import { InlineError, InlineLoading } from "../components/common";
import { ProjectCard } from "../components/ProjectCard";
import { SubpageHeader, tint } from "../components/ui";
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
      <SubpageHeader onBack={back} title={t("nav.learn")} />
      {category && (
        <section className="card card--soft row" style={{ ...tint(category.color, "1f"), gap: 14, marginBottom: 16 }}>
          <span className="emoji" aria-hidden="true" style={{ fontSize: 44 }}>
            {category.icon}
          </span>
          <div>
            <h1>{tr(category.name)}</h1>
            {category.examples && <p className="text-2">{tr(category.examples)}</p>}
          </div>
        </section>
      )}
      {data.loading && !data.data && <InlineLoading />}
      {data.error !== undefined && !data.data && <InlineError error={data.error} onRetry={data.reload} />}
      {data.data && data.data.projects.length === 0 && <p className="empty">{t("category.empty")}</p>}
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
