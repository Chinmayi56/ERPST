import React, { useState } from "react";
import Sidebar from "./Sidebar";
import Header from "./Header";

export default function DashboardLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="app-shell">
      <Sidebar open={sidebarOpen} onNavigate={() => setSidebarOpen(false)} />

      {sidebarOpen && (
        <div className="sidebar-backdrop" onClick={() => setSidebarOpen(false)} aria-hidden="true" />
      )}

      <div className="app-main">
        <Header onMenuToggle={() => setSidebarOpen((v) => !v)} />
        <main className="app-content">{children}</main>
      </div>
    </div>
  );
}
