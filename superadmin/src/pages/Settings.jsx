import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const STORAGE_KEY = "strivenest_local_preferences";

function loadLocalPrefs() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : { desktopNotifications: false };
  } catch {
    return { desktopNotifications: false };
  }
}

export default function Settings() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const [prefs, setPrefs] = useState(loadLocalPrefs());

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
  }, [prefs]);

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div>
      <div className="page-header">
        <h1>Settings</h1>
        <p className="page-subtitle">Account and session preferences.</p>
      </div>

      <div className="detail-section" style={{ maxWidth: 520, marginBottom: 20 }}>
        <h2>Notification Preference</h2>
        <p className="detail-field-value" style={{ marginBottom: 12 }}>
          This preference is stored only in your browser on this device — it is not synced to
          your account yet.
        </p>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={prefs.desktopNotifications}
            onChange={(e) => setPrefs({ ...prefs, desktopNotifications: e.target.checked })}
          />
          Highlight unread notifications in the sidebar
        </label>
      </div>

      <div className="detail-section" style={{ maxWidth: 520 }}>
        <h2>Session</h2>
        <p className="detail-field-value" style={{ marginBottom: 12 }}>
          Sign out of your SuperAdmin session on this device.
        </p>
        <button type="button" className="btn btn-danger" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}
