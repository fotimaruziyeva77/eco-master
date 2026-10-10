import { Download } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, exportUrl, type Stats } from "../api";
import { DayChart, Meter } from "../charts";
import { LoadError, Loading, PageHead, percent } from "../ui";

const EXPORTS = [
  ["daily", "Kunlar bo'yicha"],
  ["questions", "Savollar"],
  ["projects", "Loyihalar"],
  ["users", "Foydalanuvchilar"],
] as const;

const SOURCE_LABEL: Record<string, string> = {
  direct: "To'g'ridan-to'g'ri",
  teacher: "O'qituvchi havolasi",
  share: "Ulashilgan xabar",
  reminder: "Eslatma",
};

function Kpi({ value, label }: { value: string | number; label: string }) {
  return (
    <div className="a-card a-kpi">
      <strong>{value}</strong>
      <span>{label}</span>
    </div>
  );
}

/** Statistics (TZ 8.12) and the success criteria of the launch (TZ 19). */
export function StatsPage() {
  const [days, setDays] = useState(30);
  const stats = useLoad(() => adminApi.stats(days), [days]);
  const questions = useLoad(() => adminApi.questionStats(), []);
  const s = stats.data;

  return (
    <>
      <PageHead title="Statistika">
        <div className="a-tabs">
          {[7, 30, 90].map((d) => (
            <button key={d} type="button" className={days === d ? "a-tab active" : "a-tab"} onClick={() => setDays(d)}>
              {d} kun
            </button>
          ))}
        </div>
      </PageHead>
      {stats.loading && !s && <Loading />}
      {stats.error !== undefined && !s && <LoadError error={stats.error} onRetry={stats.reload} />}
      {s && <Overview stats={s} days={days} />}

      <section className="a-card" style={{ marginTop: 16 }}>
        <h2>Savollar bo'yicha to'g'ri javoblar</h2>
        <p className="a-help" style={{ marginBottom: 10 }}>
          Kamida 10 javobda to'g'ri javoblar 30% dan kam bo'lsa — savol juda qiyin yoki javob kaliti xato bo'lishi
          mumkin.
        </p>
        {questions.loading && !questions.data && <Loading />}
        {questions.data && (
          <div className="a-table-wrap">
            <table className="a-table">
              <thead>
                <tr>
                  <th>Savol</th>
                  <th>Mavzu</th>
                  <th className="num">Javoblar</th>
                  <th className="num">To'g'ri</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {[...questions.data]
                  .sort((a, b) => (a.flag === "hard" ? -1 : 0) - (b.flag === "hard" ? -1 : 0) || (a.rate ?? 2) - (b.rate ?? 2))
                  .map((q) => (
                    <tr key={q.id}>
                      <td>
                        <Link to={`/content/questions/${q.id}`}>{q.text}</Link>
                      </td>
                      <td className="a-small a-muted">{q.category}</td>
                      <td className="num">{q.answers}</td>
                      <td className="num">{percent(q.rate)}</td>
                      <td>
                        {q.flag === "hard" && <span className="a-pill a-pill--danger">tekshiring</span>}
                        {q.flag === "easy" && <span className="a-pill a-pill--warn">juda oson</span>}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

function Overview({ stats: s, days }: { stats: Stats; days: number }) {
  const dayKeys = s.daily.map((d) => d.day);
  const tasks = s.daily.reduce((n, d) => n + d.daily_tasks, 0);
  const active = s.daily.reduce((n, d) => n + d.dau, 0);
  return (
    <div className="a-stack">
      <div className="a-kpis" style={{ margin: 0 }}>
        <Kpi value={s.users_total} label={`jami foydalanuvchi (${s.users_onboarded} tasi to'liq ro'yxatdan o'tgan)`} />
        <Kpi value={s.new_users} label={`yangi, oxirgi ${days} kun`} />
        <Kpi value={s.dau_today} label="bugun faol (DAU)" />
        <Kpi value={s.wau} label="7 kunda faol (WAU)" />
        <Kpi value={s.mau} label="30 kunda faol (MAU)" />
        <Kpi value={percent(s.d1.rate)} label={`D1 (${s.d1.value}/${s.d1.size})`} />
        <Kpi value={percent(s.d7.rate)} label={`D7 (${s.d7.value}/${s.d7.size})`} />
        <Kpi value={percent(active ? tasks / active : null)} label="faollar kunlik topshiriqni bajargan" />
      </div>

      <div className="a-grid-2">
        <section className="a-card">
          <h2>Muvaffaqiyat mezonlari (TZ 19)</h2>
          <table className="a-table">
            <thead>
              <tr>
                <th>Mezon</th>
                <th className="num">Maqsad</th>
                <th className="num">Hozir</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {s.criteria.map((c) => (
                <tr key={c.key}>
                  <td>{c.label}</td>
                  <td className="num">{c.unit === "percent" ? `≥ ${Math.round(c.target * 100)}%` : `≥ ${c.target}`}</td>
                  <td className="num">{c.unit === "percent" ? percent(c.value) : (c.value ?? "—")}</td>
                  <td>
                    {c.ok === true && <span className="a-pill a-pill--ok">✓</span>}
                    {c.ok === false && <span className="a-pill a-pill--danger">✗</span>}
                    {c.ok === null && <span className="a-pill a-pill--draft">ma'lumot yo'q</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="a-help" style={{ marginTop: 8 }}>
            Davr: oxirgi {days} kunda ro'yxatdan o'tganlar.
          </p>
        </section>
        <section className="a-card">
          <h2>Onboarding voronkasi</h2>
          <div className="a-stack">
            <Meter label="Ilovani ochdi" value={s.funnel.started} total={s.funnel.started} />
            <Meter label="Til tanladi" value={s.funnel.language} total={s.funnel.started} />
            <Meter label="Yo'l tanladi" value={s.funnel.path} total={s.funnel.started} />
            <Meter label="Taxallus kiritdi" value={s.funnel.nickname} total={s.funnel.started} />
            <Meter label="Tugatdi" value={s.funnel.done} total={s.funnel.started} />
          </div>
        </section>
      </div>

      <div className="a-grid-2">
        <section className="a-card">
          <h2>Faollik</h2>
          <DayChart
            title="Kunlik faol va yangi foydalanuvchilar"
            days={dayKeys}
            series={[
              { label: "Faol (DAU)", color: "var(--primary-strong)", values: s.daily.map((d) => d.dau) },
              { label: "Yangi", color: "var(--sky)", values: s.daily.map((d) => d.new_users) },
            ]}
          />
        </section>
        <section className="a-card">
          <h2>Bajarilganlar</h2>
          <DayChart
            title="Kunlik topshiriqlar va loyihalar"
            days={dayKeys}
            series={[
              { label: "Kunlik topshiriq", color: "var(--amber)", values: s.daily.map((d) => d.daily_tasks), kind: "bar" },
              { label: "Loyiha", color: "var(--primary)", values: s.daily.map((d) => d.projects_done), kind: "bar" },
            ]}
          />
        </section>
      </div>

      <div className="a-grid-2">
        <section className="a-card">
          <h2>Eng ko'p ko'rilgan video darslar</h2>
          <table className="a-table">
            <thead>
              <tr>
                <th>Loyiha</th>
                <th className="num">Ko'rishlar</th>
                <th className="num">Odam</th>
                <th className="num">Bajardi</th>
              </tr>
            </thead>
            <tbody>
              {s.projects.slice(0, 10).map((p) => (
                <tr key={p.id}>
                  <td>
                    <Link to={`/content/projects/${p.id}`}>{p.title}</Link>
                  </td>
                  <td className="num">{p.views}</td>
                  <td className="num">{p.viewers}</td>
                  <td className="num">{p.done}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
        <div className="a-stack">
          <section className="a-card">
            <h2>O'qituvchi darslari (PDF)</h2>
            <table className="a-table">
              <thead>
                <tr>
                  <th>Dars</th>
                  <th className="num">Chatga</th>
                  <th className="num">Yuklab olingan</th>
                </tr>
              </thead>
              <tbody>
                {s.lessons.map((l) => (
                  <tr key={l.slug}>
                    <td>{l.title}</td>
                    <td className="num">{l.sent_to_chat}</td>
                    <td className="num">{l.downloads}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
          <section className="a-card">
            <h2>Qayerdan kelishdi</h2>
            <table className="a-table">
              <tbody>
                {s.sources.map((src) => (
                  <tr key={src.source}>
                    <td>{SOURCE_LABEL[src.source] ?? src.source}</td>
                    <td className="num">{src.users}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {s.sources.length === 0 && <p className="a-empty">Yangi foydalanuvchi yo'q</p>}
          </section>
        </div>
      </div>

      <section className="a-card">
        <h2>CSV eksport</h2>
        <div className="a-row">
          {EXPORTS.map(([kind, label]) => (
            <a key={kind} className="a-btn a-btn--ghost a-btn--sm" href={exportUrl(kind, days)} download>
              <Download size={14} /> {label}
            </a>
          ))}
        </div>
        <p className="a-help" style={{ marginTop: 8 }}>
          Foydalanuvchilar ro'yxatida Telegram ID va boshqa shaxsiy ma'lumotlar yo'q.
        </p>
      </section>
    </div>
  );
}
