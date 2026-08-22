import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

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
        ☰
      </button>

      <div className="header-spacer" />

      <div className="header-user">
        <span className="header-user-name">{user?.name || "Employee"}</span>
        <span className="header-user-role">EMPLOYEE</span>
        <button type="button" className="btn btn-secondary btn-small" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </header>
  );
}
