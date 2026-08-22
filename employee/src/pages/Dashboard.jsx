import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getMyDashboard, listMyNotifications } from "../api/portal";
import Loader from "../components/Loader";
import StatusBadge from "../components/StatusBadge";
import EmptyState from "../components/EmptyState";
import { myTasks, myProjects, myClients, attendanceSummary } from "../data/demoPortalData";

const SUMMARY_CARDS = [
  { key: "tasks", label: "Open Tasks", icon: "✅", value: myTasks.filter((t) => t.status !== "DONE").length },
  { key: "projects", label: "Active Projects", icon: "📁", value: myProjects.filter((p) => p.status === "ACTIVE").length },
  { key: "clients", label: "My Clients", icon: "🤝", value: myClients.length },
  { key: "attendance", label: "Present Days (This Month)", icon: "🗓️", value: `${attendanceSummary.present_days}/${attendanceSummary.working_days}` },
];

const QUICK_ACTIONS = [
  { to: "/tasks", label: "View My Tasks" },
  { to: "/projects", label: "View My Projects" },
  { to: "/leave", label: "Apply for Leave" },
  { to: "/attendance", label: "View Attendance" },
  { to: "/payslips", label: "View Payslips" },
  { to: "/profile", label: "Edit My Profile" },
];

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    getMyDashboard()
      .then(setData)
      .catch(() => setError("Could not load your dashboard."))
      .finally(() => setLoading(false));

    // Recent notifications use the real backend endpoint, same as the
    // Notifications page — only the "most recent few" slice is new here.
    listMyNotifications()
      .then((list) => setNotifications(list.slice(0, 4)))
      .catch(() => {
        // Non-critical for the dashboard; the panel just shows an empty state.
      });
  }, []);

  if (loading) return <Loader fullPage label="Loading your dashboard..." />;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!data) return null;

  const recentTasks = myTasks.slice(0, 3);
  const recentProjects = myProjects.slice(0, 3);

  return (
    <div>
      <div className="page-header">
        <h1>Welcome, {data.name}</h1>
        <p className="page-subtitle">
          {data.employee_id} · {data.department || "—"} · {data.designation || "—"} ·{" "}
          <StatusBadge status={data.status} />
        </p>
      </div>

      <div className="stat-grid">
        {SUMMARY_CARDS.map((card) => (
          <div className="stat-card" key={card.key}>
            <span className="stat-icon" aria-hidden="true">
              {card.icon}
            </span>
            <div>
              <p className="stat-value">{card.value}</p>
              <p className="stat-label">{card.label}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-panels">
        <div className="panel">
          <div className="panel-header">
            <h2>Recent Tasks</h2>
            <Link to="/tasks" className="panel-link">
              View all
            </Link>
          </div>
          {recentTasks.length ? (
            <ul className="simple-list">
              {recentTasks.map((task) => (
                <li key={task.id} className="simple-list-item">
                  <div>
                    <p className="simple-list-title">{task.title}</p>
                    <p className="simple-list-subtitle">{task.project} · Due {task.due_date}</p>
                  </div>
                  <StatusBadge status={task.status} />
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No tasks yet." />
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Recent Projects</h2>
            <Link to="/projects" className="panel-link">
              View all
            </Link>
          </div>
          {recentProjects.length ? (
            <ul className="simple-list">
              {recentProjects.map((project) => (
                <li key={project.id} className="simple-list-item">
                  <div>
                    <p className="simple-list-title">{project.name}</p>
                    <p className="simple-list-subtitle">{project.client} · {project.progress}% complete</p>
                  </div>
                  <StatusBadge status={project.status} />
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No projects yet." />
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Recent Notifications</h2>
            <Link to="/notifications" className="panel-link">
              View all
            </Link>
          </div>
          {notifications.length ? (
            <ul className="simple-list">
              {notifications.map((n) => (
                <li key={n.notification_id} className="simple-list-item">
                  <div>
                    <p className="simple-list-title">{n.message}</p>
                    <p className="simple-list-subtitle">{new Date(n.created_date).toLocaleString()}</p>
                  </div>
                  {!n.is_read && <span className="badge badge-pending">New</span>}
                </li>
              ))}
            </ul>
          ) : (
            <EmptyState title="No notifications yet." />
          )}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>Quick Actions</h2>
          </div>
          <div className="table-actions" style={{ flexWrap: "wrap" }}>
            {QUICK_ACTIONS.map((action) => (
              <Link key={action.to} to={action.to} className="btn btn-secondary btn-small">
                {action.label}
              </Link>
            ))}
          </div>
        </div>
      </div>

      <section className="detail-section" style={{ marginTop: 20 }}>
        <h2>Your Details</h2>
        <div className="detail-field">
          <span className="detail-field-label">Employee ID</span>
          <span className="detail-field-value">{data.employee_id}</span>
        </div>
        <div className="detail-field">
          <span className="detail-field-label">Email</span>
          <span className="detail-field-value">{data.email}</span>
        </div>
        <div className="detail-field">
          <span className="detail-field-label">Mobile</span>
          <span className="detail-field-value">{data.mobile}</span>
        </div>
        <div className="detail-field">
          <span className="detail-field-label">Joining Date</span>
          <span className="detail-field-value">{data.joining_date || "—"}</span>
        </div>
        <div className="detail-field">
          <span className="detail-field-label">Last Login</span>
          <span className="detail-field-value">
            {data.last_login ? new Date(data.last_login).toLocaleString() : "—"}
          </span>
        </div>
      </section>
    </div>
  );
}
