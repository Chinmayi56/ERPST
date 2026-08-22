import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboardSummary } from "../api/dashboard";
import Loader from "../components/Loader";

const SECTIONS = [
  {
    key: "new",
    title: "New Applications",
    description: "Applications submitted and awaiting first review.",
    statKey: "pending_applications",
    to: "/employee-applications",
  },
  {
    key: "pending",
    title: "Pending Applications",
    description: "Applications currently pending a decision.",
    statKey: "pending_applications",
    to: "/employee-applications",
  },
  {
    key: "approved",
    title: "Approved Employees",
    description: "Applications approved and converted to employees.",
    statKey: "approved_applications",
    to: "/employee-applications",
  },
  {
    key: "rejected",
    title: "Rejected Applications",
    description: "Applications that were reviewed and rejected.",
    statKey: "rejected_applications",
    to: "/employee-applications",
  },
  {
    key: "active",
    title: "Active Employees",
    description: "Employees currently active in the organization.",
    statKey: "active_employees",
    to: "/employees",
  },
  {
    key: "disabled",
    title: "Disabled Employees",
    description: "Employee accounts that have been disabled.",
    statKey: "disabled_employees",
    to: "/employees",
  },
];

export default function EmployeeManagement() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch(() => setError("Could not load overview data."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader fullPage label="Loading overview..." />;

  return (
    <div>
      <div className="page-header">
        <h1>Employee Management</h1>
        <p className="page-subtitle">Overview of applications and employees across the organization.</p>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="section-grid">
        {SECTIONS.map((section) => (
          <Link to={section.to} key={section.key} className="section-card">
            <div className="section-card-count">{summary?.[section.statKey] ?? 0}</div>
            <div className="section-card-title">{section.title}</div>
            <div className="section-card-description">{section.description}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
