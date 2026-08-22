import React, { useEffect, useState } from "react";
import { getDashboardSummary } from "../api/dashboard";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";

const ROWS = [
  { key: "total_employees", label: "Total Employees" },
  { key: "pending_applications", label: "Pending Applications" },
  { key: "approved_applications", label: "Approved Applications" },
  { key: "rejected_applications", label: "Rejected Applications" },
  { key: "active_employees", label: "Active Employees" },
  { key: "disabled_employees", label: "Disabled Employees" },
];

export default function Reports() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    getDashboardSummary()
      .then(setSummary)
      .catch(() => setError("Could not load report data."))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader fullPage label="Loading reports..." />;
  if (error) return <div className="alert alert-error">{error}</div>;

  const hasAnyData = ROWS.some((row) => (summary?.[row.key] ?? 0) > 0);

  return (
    <div>
      <div className="page-header">
        <h1>Reports</h1>
        <p className="page-subtitle">Summary report generated from live MongoDB data.</p>
      </div>

      {!hasAnyData ? (
        <EmptyState title="No report data available yet." />
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Metric</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row) => (
                <tr key={row.key}>
                  <td>{row.label}</td>
                  <td>{summary?.[row.key] ?? 0}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
