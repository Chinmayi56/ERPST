import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { listEmployees, disableEmployee } from "../api/employees";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";

const FILTERS = [
  { value: "", label: "All" },
  { value: "ACTIVE", label: "Active" },
  { value: "DISABLED", label: "Disabled" },
];

export default function Employees() {
  const [statusFilter, setStatusFilter] = useState("");
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [disableTarget, setDisableTarget] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    listEmployees(statusFilter || undefined)
      .then(setEmployees)
      .catch(() => setError("Could not load employees. Please try again."))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleDisable = async () => {
    setActionLoading(true);
    setActionError("");
    try {
      await disableEmployee(disableTarget.employee_id);
      setDisableTarget(null);
      load();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Could not disable employee.");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1>Employees</h1>
        <p className="page-subtitle">All employees registered in the organization.</p>
      </div>

      <div className="filter-bar">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            className={"filter-chip" + (statusFilter === f.value ? " filter-chip-active" : "")}
            onClick={() => setStatusFilter(f.value)}
            type="button"
          >
            {f.label}
          </button>
        ))}
      </div>

      {actionError && <div className="alert alert-error">{actionError}</div>}

      {loading ? (
        <Loader label="Loading employees..." />
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : employees.length === 0 ? (
        <EmptyState title="No employees registered yet." />
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Employee Name</th>
                <th>Email</th>
                <th>Mobile</th>
                <th>Position</th>
                <th>Department</th>
                <th>Joining Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {employees.map((emp) => (
                <tr key={emp.employee_id}>
                  <td>{emp.employee_id}</td>
                  <td>{emp.full_name}</td>
                  <td>{emp.email}</td>
                  <td>{emp.mobile}</td>
                  <td>{emp.position}</td>
                  <td>{emp.department || "—"}</td>
                  <td>{emp.joining_date || "—"}</td>
                  <td>
                    <StatusBadge status={emp.status} />
                  </td>
                  <td>
                    <div className="table-actions">
                      <Link to={`/employees/${emp.employee_id}`} className="btn btn-small btn-secondary">
                        View
                      </Link>
                      <Link
                        to={`/employees/${emp.employee_id}#portal-access`}
                        className="btn btn-small btn-secondary"
                      >
                        Portal Access
                      </Link>
                      {emp.status === "ACTIVE" && (
                        <button
                          type="button"
                          className="btn btn-small btn-danger"
                          onClick={() => setDisableTarget(emp)}
                        >
                          Disable
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <ConfirmDialog
        open={!!disableTarget}
        title="Disable Employee"
        message={disableTarget ? `Disable ${disableTarget.full_name}'s employee account?` : ""}
        confirmLabel="Disable"
        danger
        loading={actionLoading}
        onConfirm={handleDisable}
        onCancel={() => setDisableTarget(null)}
      />
    </div>
  );
}
