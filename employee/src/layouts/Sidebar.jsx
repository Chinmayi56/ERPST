import React from "react";
import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: "🏠" },
  { to: "/profile", label: "My Profile", icon: "👤" },
  { to: "/tasks", label: "My Tasks", icon: "✅" },
  { to: "/projects", label: "My Projects", icon: "📁" },
  { to: "/clients", label: "My Clients", icon: "🤝" },
  { to: "/attendance", label: "Attendance", icon: "🗓️" },
  { to: "/leave", label: "Leave Management", icon: "🌴" },
  { to: "/documents", label: "Documents", icon: "📄" },
  { to: "/payslips", label: "Payslips", icon: "💰" },
  { to: "/notifications", label: "Notifications", icon: "🔔" },
];

export default function Sidebar({ open, onNavigate }) {
  return (
    <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
      <div className="sidebar-brand">
        <img src="/logo.png" alt="Strivenest Technologies" className="sidebar-logo" />
        <div className="sidebar-brand-text">
          <span className="sidebar-brand-name">STRIVENEST</span>
          <span className="sidebar-brand-sub">EMPLOYEE PORTAL</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={({ isActive }) => "sidebar-link" + (isActive ? " sidebar-link-active" : "")}
          >
            <span className="sidebar-icon" aria-hidden="true">
              {item.icon}
            </span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
