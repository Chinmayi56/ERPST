import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listNotifications, markNotificationRead } from "../api/notifications";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";

export default function Notifications() {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = () => {
    setLoading(true);
    listNotifications()
      .then(setNotifications)
      .catch(() => setError("Could not load notifications."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleMarkRead = async (notificationId) => {
    try {
      await markNotificationRead(notificationId);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === notificationId ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      // Non-critical; leave state as-is on failure.
    }
  };

  const handleOpen = (n) => {
    if (!n.is_read) handleMarkRead(n.notification_id);
    if (n.related_application_id) {
      navigate(`/employee-applications/${n.related_application_id}`);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Notifications</h1>
        <p className="page-subtitle">System notifications for admin events.</p>
      </div>

      {loading ? (
        <Loader label="Loading notifications..." />
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : notifications.length === 0 ? (
        <EmptyState title="No notifications yet." />
      ) : (
        <ul className="notification-list">
          {notifications.map((n) => (
            <li
              key={n.notification_id}
              className={"notification-item" + (n.is_read ? "" : " notification-unread")}
              style={n.related_application_id ? { cursor: "pointer" } : undefined}
              onClick={() => n.related_application_id && handleOpen(n)}
            >
              <div>
                <p className="notification-message">{n.message}</p>
                <p className="notification-meta">
                  {n.type} · {new Date(n.created_date).toLocaleString()}
                </p>
              </div>
              {!n.is_read && (
                <button
                  type="button"
                  className="btn btn-small btn-secondary"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleMarkRead(n.notification_id);
                  }}
                >
                  Mark as read
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
