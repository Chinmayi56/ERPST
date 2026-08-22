import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { listApplications, approveApplication, rejectApplication } from "../api/applications";
import Loader from "../components/Loader";
import EmptyState from "../components/EmptyState";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";

const FILTERS = [
  { value: "", label: "All" },
  { value: "PENDING", label: "Pending" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
];

export default function EmployeeApplications() {
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");

  const [approveTarget, setApproveTarget] = useState(null);
  const [rejectTarget, setRejectTarget] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError("");
    listApplications(statusFilter || undefined)
      .then(setApplications)
      .catch(() => setError("Could not load applications. Please try again."))
      .finally(() => setLoading(false));
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const handleApprove = async () => {
    setActionLoading(true);
    setActionError("");
    try {
      await approveApplication(approveTarget.application_id);
      setApproveTarget(null);
      load();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Could not approve application.");
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async (reason) => {
    setActionLoading(true);
    setActionError("");
    try {
      await rejectApplication(rejectTarget.application_id, reason);
      setRejectTarget(null);
      load();
    } catch (err) {
      setActionError(err.response?.data?.detail || "Could not reject application.");
    } finally {
      setActionLoading(false);
    }
  };

  const visibleApplications = applications.filter((app) => {
    if (!search.trim()) return true;
    const q = search.trim().toLowerCase();
    return (
      app.application_id?.toLowerCase().includes(q) ||
      app.full_name?.toLowerCase().includes(q) ||
      app.email?.toLowerCase().includes(q) ||
      app.mobile?.toLowerCase().includes(q)
    );
  });

  return (
    <div>
      <div className="page-header">
        <h1>Employee Applications</h1>
        <p className="page-subtitle">Review, approve, or reject incoming employee applications.</p>
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

      <div className="form-group" style={{ maxWidth: 340 }}>
        <input
          type="text"
          placeholder="Search by name, email, mobile, or application ID"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {actionError && <div className="alert alert-error">{actionError}</div>}

      {loading ? (
        <Loader label="Loading applications..." />
      ) : error ? (
        <div className="alert alert-error">{error}</div>
      ) : applications.length === 0 ? (
        <EmptyState title="No employee applications yet." />
      ) : visibleApplications.length === 0 ? (
        <EmptyState title="No applications match your search." />
      ) : (
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Application ID</th>
                <th>Employee Name</th>
                <th>Email</th>
                <th>Mobile</th>
                <th>Applied Position</th>
                <th>Department</th>
                <th>Experience</th>
                <th>Submitted Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {visibleApplications.map((app) => (
                <tr key={app.application_id}>
                  <td>{app.application_id}</td>
                  <td>{app.full_name}</td>
                  <td>{app.email}</td>
                  <td>{app.mobile}</td>
                  <td>{app.applied_position}</td>
                  <td>{app.department || "—"}</td>
                  <td>{app.total_experience || app.experience_level || "—"}</td>
                  <td>{new Date(app.submitted_date).toLocaleDateString()}</td>
                  <td>
                    <StatusBadge status={app.status} />
                  </td>
                  <td>
                    <div className="table-actions">
                      <Link to={`/employee-applications/${app.application_id}`} className="btn btn-small btn-secondary">
                        View
                      </Link>
                      {app.status === "PENDING" && (
                        <>
                          <button
                            type="button"
                            className="btn btn-small btn-primary"
                            onClick={() => setApproveTarget(app)}
                          >
                            Approve
                          </button>
                          <button
                            type="button"
                            className="btn btn-small btn-danger"
                            onClick={() => setRejectTarget(app)}
                          >
                            Reject
                          </button>
                        </>
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
        open={!!approveTarget}
        title="Approve Application"
        message={approveTarget ? `Approve the application from ${approveTarget.full_name}? An employee record will be created.` : ""}
        confirmLabel="Approve"
        loading={actionLoading}
        onConfirm={handleApprove}
        onCancel={() => setApproveTarget(null)}
      />

      <ConfirmDialog
        open={!!rejectTarget}
        title="Reject Application"
        message={rejectTarget ? `Reject the application from ${rejectTarget.full_name}?` : ""}
        confirmLabel="Reject"
        danger
        requireReason
        loading={actionLoading}
        onConfirm={handleReject}
        onCancel={() => setRejectTarget(null)}
      />
    </div>
  );
}
