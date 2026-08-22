import {
  BarChart3,
  Bookmark,
  Search,
} from "lucide-react";
import { NavLink } from "react-router";
import type { ReactNode } from "react";

interface AppShellProps {
  children: ReactNode;
}

const navigation = [
  {
    icon: BarChart3,
    label: "Dashboard",
    to: "/",
  },
  {
    icon: Search,
    label: "Explorer",
    to: "/explorer",
  },
  {
    icon: Bookmark,
    label: "Watchlists",
    to: "/watchlist",
  },
];

export function AppShell({ children }: AppShellProps) {
  return (
    <div className="app-shell">
      <header className="app-topbar">
        <div className="app-topbar-inner">
          <NavLink className="brand" to="/">
            <span className="brand-mark">SI</span>
            <span>Stable Indexer</span>
          </NavLink>

          <nav aria-label="Primary navigation" className="primary-nav">
            {navigation.map(({ icon: Icon, label, to }) => (
              <NavLink
                className={({ isActive }) => (
                  `primary-nav-link${isActive ? " active" : ""}`
                )}
                end={to === "/"}
                key={label}
                to={to}
              >
                <Icon aria-hidden="true" size={16} strokeWidth={2} />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      {children}
    </div>
  );
}
