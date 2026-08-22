import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getEmployee, updateEmployee, disableEmployee } from "../api/employees";
import Loader from "../components/Loader";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";
import EmployeePortalAccess from "../components/EmployeePortalAccess";

export default function EmployeeDetail() {
  const { employeeId } = useParams();

  const [employee, setEmployee] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ full_name: "", mobile: "", position: "", department: "" });
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [disableOpen, setDisableOpen] = useState(false);

  const load = () => {
    setLoading(true);
    getEmployee(employeeId)
      .then((data) => {
        setEmployee(data);
        setForm({
          full_name: data.full_name || "",
          mobile: data.mobile || "",
          position: data.position || "",
          department: data.department || "",
        });
      })
      .catch(() => setError("Could not load this employee."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [employeeId]);

  useEffect(() => {
    if (!loading && window.location.hash === "#portal-access") {
      document.getElementById("portal-access")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [loading]);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveError("");
    try {
      await updateEmployee(employeeId, form);
      setEditing(false);
      load();
    } catch (err) {
      setSaveError(err.response?.data?.detail || "Could not save changes.");
    } finally {
      setSaving(false);
    }
  };

  const handleDisable = async () => {
    setSaving(true);
    try {
      await disableEmployee(employeeId);
      setDisableOpen(false);
      load();
    } catch (err) {
      setSaveError(err.response?.data?.detail || "Could not disable employee.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Loader fullPage label="Loading employee..." />;
  if (error) return <div className="alert alert-error">{error}</div>;
  if (!employee) return null;

  return (
    <div>
      <div className="page-header">
        <div>
          <Link to="/employees" className="back-link">
            ← Back to Employees
          </Link>
          <h1>{employee.full_name}</h1>
          <p className="page-subtitle">
            {employee.employee_id} · <StatusBadge status={employee.status} />
          </p>
        </div>
        <div className="table-actions">
          {!editing && (
            <button type="button" className="btn btn-secondary" onClick={() => setEditing(true)}>
              Edit
            </button>
          )}
          {employee.status === "ACTIVE" && (
            <button type="button" className="btn btn-danger" onClick={() => setDisableOpen(true)}>
              Disable
            </button>
          )}
        </div>
      </div>

      {saveError && <div className="alert alert-error">{saveError}</div>}

      {editing ? (
        <form onSubmit={handleSave} className="detail-section" style={{ maxWidth: 480 }}>
          <div className="form-group">
            <label htmlFor="full_name">Full Name</label>
            <input
              id="full_name"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="mobile">Mobile</label>
            <input
              id="mobile"
              value={form.mobile}
              onChange={(e) => setForm({ ...form, mobile: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label htmlFor="position">Position</label>
            <input
              id="position"
              value={form.position}
              onChange={(e) => setForm({ ...form, position: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label htmlFor="department">Department</label>
            <input
              id="department"
              value={form.department}
              onChange={(e) => setForm({ ...form, department: e.target.value })}
            />
          </div>
          <div className="table-actions">
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving ? "Saving..." : "Save Changes"}
            </button>
            <button type="button" className="btn btn-secondary" onClick={() => setEditing(false)} disabled={saving}>
              Cancel
            </button>
          </div>
        </form>
      ) : (
        <div className="detail-grid">
          <section className="detail-section">
            <h2>Employee Profile</h2>
            <div className="detail-field">
              <span className="detail-field-label">Employee ID</span>
              <span className="detail-field-value">{employee.employee_id}</span>
            </div>
            <div className="detail-field">
              <span className="detail-field-label">Full Name</span>
              <span className="detail-field-value">{employee.full_name}</span>
            </div>
            <div className="detail-field">
              <span className="detail-field-label">Email</span>
              <span className="detail-field-value">{employee.email}</span>
            </div>
            <div className="detail-field">
              <span className="detail-field-label">Mobile</span>
              <span className="detail-field-value">{employee.mobile}</span>
            </div>
            <div className="detail-field">
              <span className="detail-field-label">Position</span>
              <span className="detail-field-value">{employee.position}</span>
            </div>
            <div className="detail-field">
              <span className="detail-field-label">Department</span>
              <span className="detail-field-value">{employee.department || "—"}</span>
            </div>
            <div className="detail-field">
              <span className="detail-field-label">Joining Date</span>
              <span className="detail-field-value">{employee.joining_date || "—"}</span>
            </div>
            <div className="detail-field">
              <span className="detail-field-label">Source Application</span>
              <span className="detail-field-value">{employee.source_application_id || "—"}</span>
            </div>
          </section>

          <EmployeePortalAccess employee={employee} />

          <section className="detail-section">
            <h2>Documents</h2>
            <p className="detail-field-value">
              Document viewing will be available once the Employee Registration Form portal is
              live and documents are uploaded.
            </p>
          </section>
        </div>
      )}

      <ConfirmDialog
        open={disableOpen}
        title="Disable Employee"
        message={`Disable ${employee.full_name}'s employee account?`}
        confirmLabel="Disable"
        danger
        loading={saving}
        onConfirm={handleDisable}
        onCancel={() => setDisableOpen(false)}
      />
    </div>
  );
}
