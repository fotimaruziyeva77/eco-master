import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";

import { useLoad } from "../../hooks/useLoad";
import { adminApi, errorText } from "../api";
import { fmtDate, LoadError, Loading, PageHead, useToast } from "../ui";

type Kind = "daily" | "tips";
const WEEKDAYS = ["Yak", "Du", "Se", "Chor", "Pay", "Ju", "Shan"];

function isoDay(date: Date): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Tashkent" }).format(date);
}

function shift(day: string, days: number): string {
  const d = new Date(`${day}T12:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

/** Which task and tip each date gets; empty dates follow the rotation (TZ 8.5). */
export function SchedulePage() {
  const toast = useToast();
  const today = isoDay(new Date());
  const [kind, setKind] = useState<Kind>("daily");
  const [start, setStart] = useState(today);
  const schedule = useLoad(() => adminApi.schedule(kind, start), [kind, start]);

  async function pick(day: string, value: string) {
    try {
      await adminApi.setSchedule(kind, day, value ? Number(value) : null);
      toast(value ? "Sanaga biriktirildi" : "Avtomatik tanlovga qaytarildi");
      schedule.reload();
    } catch (e) {
      toast(errorText(e));
    }
  }

  return (
    <>
      <PageHead title="Kunlik jadval" />
      <div className="a-toolbar">
        <div className="a-tabs">
          <button type="button" className={kind === "daily" ? "a-tab active" : "a-tab"} onClick={() => setKind("daily")}>
            Kunlik topshiriqlar
          </button>
          <button type="button" className={kind === "tips" ? "a-tab active" : "a-tab"} onClick={() => setKind("tips")}>
            Maslahatlar
          </button>
        </div>
        <span className="a-row" style={{ marginLeft: "auto" }}>
          <button type="button" className="a-icon-btn" onClick={() => setStart(shift(start, -35))} aria-label="Oldingi davr">
            <ChevronLeft size={16} />
          </button>
          <button type="button" className="a-btn a-btn--ghost a-btn--sm" onClick={() => setStart(today)}>
            Bugun
          </button>
          <button type="button" className="a-icon-btn" onClick={() => setStart(shift(start, 35))} aria-label="Keyingi davr">
            <ChevronRight size={16} />
          </button>
        </span>
      </div>
      <p className="a-help" style={{ marginBottom: 12 }}>
        Sanaga hech narsa biriktirilmasa, nashr qilinganlar ro'yxatidan navbatdagisi avtomatik tanlanadi. Hamma
        foydalanuvchi bir kunda bir xil topshiriqni oladi.
      </p>

      {schedule.loading && !schedule.data && <Loading />}
      {schedule.error !== undefined && !schedule.data && <LoadError error={schedule.error} onRetry={schedule.reload} />}
      {schedule.data && (
        <div className="a-table-wrap">
          <table className="a-table">
            <thead>
              <tr>
                <th>Sana</th>
                <th>{kind === "daily" ? "Topshiriq" : "Maslahat"}</th>
              </tr>
            </thead>
            <tbody>
              {schedule.data.days.map((d) => (
                <tr key={d.day} style={d.day === today ? { background: "var(--primary-soft)" } : undefined}>
                  <td className="a-small" style={{ whiteSpace: "nowrap" }}>
                    <strong>{fmtDate(d.day)}</strong> <span className="a-muted">{WEEKDAYS[new Date(`${d.day}T12:00:00Z`).getUTCDay()]}</span>
                    {d.day === today && <span className="a-pill a-pill--ok" style={{ marginLeft: 6 }}>bugun</span>}
                  </td>
                  <td>
                    <select className="a-select" value={d.item_id ?? ""} onChange={(e) => void pick(d.day, e.target.value)}>
                      <option value="">Avtomatik: {d.auto_item_title ?? "—"}</option>
                      {schedule.data!.items.map((item) => (
                        <option key={item.id} value={item.id}>
                          {item.title}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {schedule.data.items.length === 0 && <p className="a-empty">Nashr qilingan kontent yo'q.</p>}
        </div>
      )}
    </>
  );
}
