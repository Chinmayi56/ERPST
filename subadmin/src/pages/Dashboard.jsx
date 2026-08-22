import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboardSummary } from "../api/dashboard";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import StatusBadge from "../components/StatusBadge";
import {
  IconUsers,
  IconClock,
  IconUserCheck,
  IconBell,
  IconLayers,
  IconFileText,
  IconCheckCircle,
  IconCheckSquare,
} from "../components/Icons";

const CARD_DEFS = [
  { key: "total_employees", label: "Employees", icon: IconUsers, tone: "blue" },
  { key: "active_employees", label: "Active Employees", icon: IconUserCheck, tone: "teal" },
  { key: "pending_employees", label: "Pending Employees", icon: IconClock, tone: "amber" },
  { key: "clients_total", label: "Clients", icon: IconLayers, tone: "violet" },
  { key: "active_projects", label: "Active Projects", icon: IconCheckCircle, tone: "green" },
  { key: "pending_tasks", label: "Pending Tasks", icon: IconCheckSquare, tone: "amber" },
  { key: "pending_leaves", label: "Pending Leaves", icon: IconClock, tone: "red" },
  { key: "unread_notifications", label: "Notifications", icon: IconBell, tone: "violet" },
  { key: "today_attendance", label: "Today Attendance", icon: IconClock, tone: "teal" },
  { key: "active_services", label: "Active Services", icon: IconLayers, tone: "blue" },
  { key: "active_bookings", label: "Active Bookings", icon: IconFileText, tone: "green" },
  { key: "documents_total", label: "Documents", icon: IconFileText, tone: "violet" },
];

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    getDashboardSummary()
      .then((data) => {
        if (mounted) setSummary(data);
      })
      .catch(() => {
        if (mounted) setError("Could not load dashboard data. Please try again.");
      })
      .finally(() => {
        if (mounted) setLoading(false);
      });
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <Loader fullPage label="Loading dashboard..." />;
  if (error) return <div className="alert alert-error">{error}</div>;

  return (
    <div>
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="page-subtitle">Real-time overview of Strivenest Technologies operations.</p>
      </div>

      <div className="stat-grid">
        {CARD_DEFS.map((card) => {
          const CardIcon = card.icon;
          const rawValue = summary?.[card.key];
          const displayValue = rawValue ?? 0;
          return (
            <div className="stat-card" key={card.key}>
              <span className={`stat-icon-wrap stat-icon-${card.tone}`} aria-hidden="true">
                <CardIcon />
              </span>
              <div>
                <p className="stat-value">{displayValue}</p>
                <p className="stat-label">
                  {card.label}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      <div className="dashboard-panels">
        <div className="panel">
          <div className="panel-header">
            <h2>Recent Activities</h2>
          </div>
          {summary?.recent_activities?.length ? (
            <ul className="simple-list">
              {summary.recent_activities.map((activity) => (
                <li key={activity.audit_id} className="simple-list-item">
                  <div>
                    <p className="simple-list-title">{activity.label}</p>
                    <p className="simple-list-subtitle">
                      {activity.role} · {new Date(activity.timestamp).toLocaleString()}
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No recent activity yet." />
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Recent Applications</h2>
            <Link to="/employee-applications" className="panel-link">
              View all
            </Link>
          </div>
          {summary?.recent_applications?.length ? (
            <ul className="simple-list">
              {summary.recent_applications.map((app) => (
                <li key={app.application_id} className="simple-list-item">
                  <div>
                    <p className="simple-list-title">{app.full_name}</p>
                    <p className="simple-list-subtitle">{app.applied_position}</p>
                  </div>
                  <StatusBadge status={app.status} />
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No employee applications yet." />
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Recent Notifications</h2>
            <Link to="/notifications" className="panel-link">
              View all
            </Link>
          </div>
          {summary?.recent_notifications?.length ? (
            <ul className="simple-list">
              {summary.recent_notifications.map((n) => (
                <li key={n.notification_id} className="simple-list-item">
                  <div>
                    <p className="simple-list-title">{n.message}</p>
                  </div>
                  {!n.is_read && <span className="badge badge-pending">New</span>}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No notifications yet." />
          )}
        </div>
      </div>
    </div>
  );
}
