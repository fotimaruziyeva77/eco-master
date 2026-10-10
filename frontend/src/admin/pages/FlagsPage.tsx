import { useState } from "react";
import { Link } from "react-router";

import { useLoad } from "../../hooks/useLoad";
import { adminApi } from "../api";
import { fmtDate, LoadError, Loading, PageHead } from "../ui";

/** Suspicious activity (TZ 11.1): more than 300 points a day, or unnaturally fast answers. */
export function FlagsPage() {
  const [days, setDays] = useState(14);
  const flags = useLoad(() => adminApi.flags(days), [days]);
  return (
    <>
      <PageHead title="Shubhali faollik">
        <div className="a-tabs">
          {[7, 14, 30].map((d) => (
            <button key={d} type="button" className={days === d ? "a-tab active" : "a-tab"} onClick={() => setDays(d)}>
              {d} kun
            </button>
          ))}
        </div>
      </PageHead>
      <p className="a-help" style={{ marginBottom: 14 }}>
        Bu avtomatik belgi, ayblov emas. Foydalanuvchi kartochkasida faoliyatni ko'rib, kerak bo'lsa soxta
        ballarni bekor qiling.
      </p>
      {flags.loading && !flags.data && <Loading />}
      {flags.error !== undefined && !flags.data && <LoadError error={flags.error} onRetry={flags.reload} />}
      {flags.data && (
        <div className="a-grid-2">
          <section className="a-card">
            <h2>Bir kunda 300 balldan ko'p</h2>
            {flags.data.points.length === 0 ? (
              <p className="a-empty">Yo'q</p>
            ) : (
              <table className="a-table">
                <thead>
                  <tr>
                    <th>Foydalanuvchi</th>
                    <th>Kun</th>
                    <th className="num">Ball</th>
                  </tr>
                </thead>
                <tbody>
                  {flags.data.points.map((f) => (
                    <tr key={`${f.user_id}-${f.day}`}>
                      <td>
                        <Link to={`/users/${f.user_id}`}>@{f.nickname ?? f.user_id}</Link>
                      </td>
                      <td>{fmtDate(f.day)}</td>
                      <td className="num">{f.points}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
          <section className="a-card">
            <h2>Juda tez javoblar</h2>
            <p className="a-help" style={{ marginBottom: 8 }}>
              Raundda o'rtacha 1 soniyadan tez (kamida 5 ta javob).
            </p>
            {flags.data.fast.length === 0 ? (
              <p className="a-empty">Yo'q</p>
            ) : (
              <table className="a-table">
                <thead>
                  <tr>
                    <th>Foydalanuvchi</th>
                    <th>O'yin</th>
                    <th>Kun</th>
                    <th className="num">Javob</th>
                    <th className="num">O'rtacha</th>
                  </tr>
                </thead>
                <tbody>
                  {flags.data.fast.map((f, i) => (
                    <tr key={i}>
                      <td>
                        <Link to={`/users/${f.user_id}`}>@{f.nickname ?? f.user_id}</Link>
                      </td>
                      <td>{f.game === "quiz" ? "Viktorina" : "Saralash"}</td>
                      <td>{fmtDate(f.day)}</td>
                      <td className="num">{f.answers}</td>
                      <td className="num">{f.avg_seconds.toFixed(2)} s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </div>
      )}
    </>
  );
}
