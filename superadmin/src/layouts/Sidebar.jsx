import React from "react";
import { NavLink } from "react-router-dom";
import {
  IconHome,
  IconLayers,
  IconFileText,
  IconUsers,
  IconLink,
  IconBell,
  IconBarChart,
  IconUser,
  IconSettings,
  IconBriefcase,
  IconFolder,
  IconCheckSquare,
  IconCalendar,
  IconClock,
  IconClipboard,
  IconShield,
} from "../components/Icons";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: IconHome },
  { to: "/employee-management", label: "Employee Management", icon: IconLayers },
  { to: "/employees", label: "Employees", icon: IconUsers },
  { to: "/employee-applications", label: "Employee Applications", icon: IconFileText },
  { to: "/registration-forms", label: "Registration Forms", icon: IconLink },
  { to: "/clients", label: "Client Management", icon: IconBriefcase },
  { to: "/projects", label: "Project Management", icon: IconFolder },
  { to: "/tasks", label: "Task Management", icon: IconCheckSquare },
  { to: "/leave-requests", label: "Leave Requests", icon: IconCalendar },
  { to: "/attendance", label: "Attendance", icon: IconClock },
  { to: "/services", label: "Services", icon: IconClipboard },
  { to: "/services-bookings", label: "Bookings", icon: IconClipboard },
  { to: "/documents", label: "Documents", icon: IconFolder },
  { to: "/reports", label: "Reports", icon: IconBarChart },
  { to: "/notifications", label: "Notifications", icon: IconBell },
  { to: "/user-role-management", label: "User & Role Management", icon: IconShield },
  { to: "/profile", label: "My Profile", icon: IconUser },
  { to: "/settings", label: "Settings", icon: IconSettings },
];

export default function Sidebar({ open, onNavigate }) {
  return (
    <aside className={`sidebar ${open ? "sidebar-open" : ""}`}>
      <div className="sidebar-brand">
        <img src="/logo.png" alt="Strivenest Technologies" className="sidebar-logo" />
        <div className="sidebar-brand-text">
          <span className="sidebar-brand-name">STRIVENEST</span>
          <span className="sidebar-brand-sub">TECHNOLOGIES</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const ItemIcon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={({ isActive }) => "sidebar-link" + (isActive ? " sidebar-link-active" : "")}
            >
              <span className="sidebar-icon" aria-hidden="true">
                <ItemIcon size={18} />
              </span>
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}
