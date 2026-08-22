import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { IconMenu } from "../components/Icons";

function getInitials(name) {
  if (!name) return "SU";
  const parts = name.trim().split(/\s+/);
  const first = parts[0]?.[0] || "";
  const last = parts.length > 1 ? parts[parts.length - 1][0] : "";
  return (first + last).toUpperCase() || "SU";
}

export default function Header({ onMenuToggle }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <header className="app-header">
      <button
        type="button"
        className="menu-toggle-btn"
        aria-label="Toggle navigation menu"
        onClick={onMenuToggle}
      >
        <IconMenu size={22} />
      </button>

      <div className="header-spacer" />

      <div className="header-user">
        <span className="header-avatar" aria-hidden="true">
          {getInitials(user?.name)}
        </span>
        <div className="header-user-info">
          <span className="header-user-name">{user?.name || "SubAdmin"}</span>
          <span className="header-user-role">SUBADMIN</span>
        </div>
        <button type="button" className="btn btn-secondary btn-small" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}
