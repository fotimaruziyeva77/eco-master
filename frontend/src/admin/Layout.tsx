import {
  BarChart3,
  BookOpen,
  CalendarDays,
  CircleQuestionMark,
  Flag,
  GraduationCap,
  Hammer,
  KeyRound,
  Lightbulb,
  ListChecks,
  LogOut,
  MapPin,
  Megaphone,
  Menu,
  PackageCheck,
  MessageSquareWarning,
  Recycle,
  School,
  ScrollText,
  ShieldAlert,
  ShieldCheck,
  Store,
  Tags,
  Users,
  type LucideIcon,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router";

import mark from "../assets/brand/eco-master-mark.webp";
import { useLoad } from "../hooks/useLoad";
import { adminApi } from "./api";
import { ROLE_LABEL, useAdmin } from "./ui";

export const TYPE_ICONS: Record<string, LucideIcon> = {
  projects: Hammer,
  questions: CircleQuestionMark,
  "game-items": Recycle,
  "daily-tasks": ListChecks,
  tips: Lightbulb,
  cards: BookOpen,
  lessons: GraduationCap,
  categories: Tags,
  "pickup-points": MapPin,
};

function Link({ to, icon: Icon, label, count }: { to: string; icon: LucideIcon; label: string; count?: number }) {
  return (
    <NavLink to={to} className={({ isActive }) => (isActive ? "a-nav-link active" : "a-nav-link")}>
      <Icon size={18} aria-hidden="true" />
      <span>{label}</span>
      {count ? <span className="a-nav-count">{count}</span> : null}
    </NavLink>
  );
}

export function Layout({ children }: { children: ReactNode }) {
  const { me, signOut } = useAdmin();
  const { pathname } = useLocation();
  const [open, setOpen] = useState(false);
  const isAdmin = me.role === "admin";
  const isPoint = me.role === "point";
  // Counts refresh on every page change: items waiting for review, open reports.
  const types = useLoad(() => (isPoint ? Promise.resolve([]) : adminApi.contentTypes()), [pathname, isPoint]);
  const market = useLoad(() => (isPoint ? Promise.resolve(null) : adminApi.marketCounts()), [pathname, isPoint]);
  const reports = useLoad(() => (isAdmin ? adminApi.openReports() : Promise.resolve([])), [pathname, isAdmin]);

  useEffect(() => setOpen(false), [pathname]);

  return (
    <div className="a-shell">
      <header className="a-mobile-bar">
        <button type="button" className="a-icon-btn" onClick={() => setOpen(true)} aria-label="Menyu">
          <Menu size={18} />
        </button>
        Eco-Master admin
      </header>
      <nav className={open ? "a-side open" : "a-side"} aria-label="Bo'limlar">
        <div className="a-brand">
          <img className="logo" src={mark} alt="" />
          <span>
            Eco-Master
            <small>Admin panel</small>
          </span>
        </div>
        {isAdmin && <Link to="/stats" icon={BarChart3} label="Statistika" />}

        {!isPoint && (
          <>
            <div className="a-nav-title">Kontent</div>
            {types.data?.map((t) => (
              <Link
                key={t.key}
                to={`/content/${t.key}`}
                icon={TYPE_ICONS[t.key] ?? BookOpen}
                label={t.title}
                count={t.counts.review}
              />
            ))}
            <Link to="/schedule" icon={CalendarDays} label="Kunlik jadval" />
          </>
        )}

        <div className="a-nav-title">Bozor</div>
        {!isPoint && (
          <Link
            to="/market"
            icon={Store}
            label="E'lonlar moderatsiyasi"
            count={market.data ? market.data.pending + market.data.reported : undefined}
          />
        )}
        {(isAdmin || isPoint) && <Link to="/handover" icon={PackageCheck} label="Topshirish pulti" />}

        {isAdmin && (
          <>
            <div className="a-nav-title">Moderatsiya</div>
            <Link to="/users" icon={Users} label="Foydalanuvchilar" />
            <Link to="/classes" icon={School} label="Sinflar" />
            <Link to="/broadcasts" icon={Megaphone} label="Xabar yuborish" />
            <Link
              to="/reports"
              icon={MessageSquareWarning}
              label="Shikoyatlar"
              count={reports.data?.length}
            />
            <Link to="/flags" icon={ShieldAlert} label="Shubhali faollik" />
            <Link to="/words" icon={Flag} label="So'zlar ro'yxati" />
            <div className="a-nav-title">Tizim</div>
            <Link to="/audit" icon={ScrollText} label="Audit jurnali" />
            <Link to="/admins" icon={ShieldCheck} label="Adminlar" />
          </>
        )}

        <div className="a-side-foot">
          <div className="a-who">
            <strong>{me.name}</strong>
            <div className="a-muted">{ROLE_LABEL[me.role]}</div>
          </div>
          <Link to="/account" icon={KeyRound} label="Parolni o'zgartirish" />
          <button type="button" className="a-nav-link" style={{ border: 0, background: "none", width: "100%" }} onClick={signOut}>
            <LogOut size={18} aria-hidden="true" />
            Chiqish
          </button>
        </div>
      </nav>
      {open && <div className="a-backdrop" style={{ zIndex: 55 }} onClick={() => setOpen(false)} />}
      <main className="a-main">{children}</main>
    </div>
  );
}
