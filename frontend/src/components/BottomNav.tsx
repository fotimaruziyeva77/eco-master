import { Gamepad2, House, Sprout, Store, Trophy, type LucideIcon } from "lucide-react";
import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";

import { haptic } from "../telegram";

const ITEMS: { to: string; icon: LucideIcon; label: string; end: boolean }[] = [
  { to: "/", icon: House, label: "nav.home", end: true },
  { to: "/learn", icon: Sprout, label: "nav.learn", end: false },
  { to: "/games", icon: Gamepad2, label: "nav.games", end: false },
  { to: "/rating", icon: Trophy, label: "nav.rating", end: false },
  // The profile opens from the avatar in the top bar (phase 9: the market took its place).
  { to: "/market", icon: Store, label: "nav.market", end: false },
];

export function BottomNav() {
  const { t } = useTranslation();
  return (
    <nav className="bottom-nav">
      {ITEMS.map(({ to, icon: Icon, label, end }) => (
        <NavLink
          key={to}
          to={to}
          end={end}
          onClick={haptic.tap}
          className={({ isActive }) => (isActive ? "bottom-nav__item is-active" : "bottom-nav__item")}
        >
          <Icon size={22} aria-hidden="true" />
          <span>{t(label)}</span>
        </NavLink>
      ))}
    </nav>
  );
}
