import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";

import { haptic } from "../telegram";

const ITEMS = [
  { to: "/", icon: "🏠", label: "nav.home", end: true },
  { to: "/learn", icon: "📚", label: "nav.learn", end: false },
  { to: "/games", icon: "🎮", label: "nav.games", end: false },
  { to: "/rating", icon: "🏆", label: "nav.rating", end: false },
  { to: "/profile", icon: "👤", label: "nav.profile", end: false },
] as const;

export function BottomNav() {
  const { t } = useTranslation();
  return (
    <nav className="bottom-nav">
      {ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={haptic.tap}
          className={({ isActive }) => (isActive ? "bottom-nav__item is-active" : "bottom-nav__item")}
        >
          <span className="bottom-nav__icon" aria-hidden="true">
            {item.icon}
          </span>
          <span>{t(item.label)}</span>
        </NavLink>
      ))}
    </nav>
  );
}
