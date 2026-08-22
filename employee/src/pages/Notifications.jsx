import React, { useEffect, useState } from "react";
import { listMyNotifications, markMyNotificationRead, markAllMyNotificationsRead } from "../api/portal";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";

export default function Notifications() {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [markingAll, setMarkingAll] = useState(false);

  const load = () => {
    setLoading(true);
    listMyNotifications()
      .then(setNotifications)
      .catch(() => setError("Could not load notifications."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleMarkRead = async (notificationId) => {
    try {
      await markMyNotificationRead(notificationId);
      setNotifications((prev) =>
        prev.map((n) => (n.notification_id === notificationId ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      // Non-critical; leave state as-is on failure.
    }
  };

  const handleMarkAllRead = async () => {
    setMarkingAll(true);
    try {
      await markAllMyNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      // Non-critical; leave state as-is on failure.
    } finally {
      setMarkingAll(false);
    }
  };

  const hasUnread = notifications.some((n) => !n.is_read);

  return (
    <div>
      <div className="page-header">
        <h1>Notifications</h1>
        <p className="page-subtitle">Updates about your application and employee account.</p>
      </div>

      {hasUnread && (
        <div className="table-actions" style={{ marginBottom: 16 }}>
          <button
            type="button"
            className="btn btn-secondary btn-small"
            onClick={handleMarkAllRead}
            disabled={markingAll}
          >
            {markingAll ? "Marking..." : "Mark all as read"}
          </button>
        </div>
      )}

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
                  onClick={() => handleMarkRead(n.notification_id)}
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
